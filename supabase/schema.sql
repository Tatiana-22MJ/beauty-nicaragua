-- =============================================================================
-- schema.sql — Esquema Beauty Nicaragua para Supabase (Postgres)
-- =============================================================================
-- Ejecutar en Supabase Dashboard → SQL Editor → New query → Run.
-- Alternativa: la app crea las tablas automáticamente con db.create_all()
-- al arrancar (este script es la vía "DBA" y deja RLS activado).
--
-- Acceso: el backend Flask se conecta con el usuario postgres del pooler
-- (bypasea RLS). La Data API pública (anon key) NO puede leer nada porque
-- RLS está habilitado sin políticas públicas → defensa en profundidad.

-- ===== users =====
create table if not exists users (
    id            serial primary key,
    username      varchar(30)  unique not null,
    email         varchar(120) unique not null,
    password_hash varchar(256) not null,
    full_name     varchar(120) not null,
    phone         varchar(30)  default '',
    is_admin      boolean not null default false,
    created_at    timestamp not null default now()
);

-- ===== services =====
create table if not exists services (
    id               serial primary key,
    name             varchar(120) not null,
    description      text not null,
    price            double precision not null,
    currency         varchar(3)   default 'NIO',
    duration_minutes integer      default 60,
    icon             varchar(16)  default '✨',
    image_url        varchar(500) default '',
    sort_order       integer      default 0,
    is_active        boolean      default true,
    quote_only       boolean      default false,
    is_seed          boolean not null default false  -- true = catálogo base (el seed no la borra)
);

-- ===== service_packages =====
create table if not exists service_packages (
    id          serial primary key,
    name        varchar(120) not null,
    description text not null,
    includes    text default '',
    price       double precision not null,
    currency    varchar(3)   default 'NIO',
    image_url   varchar(500) default '',
    sort_order  integer      default 0,
    is_active   boolean      default true,
    is_seed     boolean not null default false
);

-- ===== bookings =====
create table if not exists bookings (
    id             serial primary key,
    user_id        integer references users(id),
    full_name      varchar(120) not null,
    email          varchar(120) not null,
    phone          varchar(30)  not null,
    service_id     integer references services(id),
    package_id     integer references service_packages(id),
    preferred_date varchar(20) not null,                 -- YYYY-MM-DD
    preferred_time varchar(10) not null default '09:00', -- HH:MM
    message        text default '',
    status         varchar(20) default 'pending',        -- pending|confirmed|cancelled|completed|reschedule
    payment_status varchar(30) default 'unpaid',         -- unpaid|pending_transfer|paid
    payment_proof  varchar(255) default '',              -- path en Supabase Storage o archivo local
    deposit_amount double precision default 0,
    admin_notes    text default '',
    created_at     timestamp not null default now(),
    updated_at     timestamp
);

-- Anti doble-reserva: una sola cita ACTIVA por fecha+hora (índice parcial).
create unique index if not exists uq_bookings_active_slot
    on bookings (preferred_date, preferred_time)
    where status in ('pending', 'confirmed', 'reschedule');

create index if not exists ix_bookings_date on bookings (preferred_date);
create index if not exists ix_bookings_user on bookings (user_id);

-- ===== chat_messages =====
create table if not exists chat_messages (
    id         serial primary key,
    user_id    integer references users(id),
    session_id varchar(64) not null,
    sender     varchar(20) not null,                     -- user|bot
    content    text not null,
    created_at timestamp not null default now()
);

create index if not exists ix_chat_messages_session on chat_messages (session_id);

-- ===== salon_info =====
create table if not exists salon_info (
    id    serial primary key,
    key   varchar(50) unique not null,
    value text not null
);

-- ===== audit_logs =====
create table if not exists audit_logs (
    id         serial primary key,
    user_id    integer references users(id),
    action     varchar(120) not null,
    detail     text default '',
    created_at timestamp not null default now()
);

-- ===== Row Level Security (defensa en profundidad) =====
-- El backend conecta como postgres (bypasea RLS). Sin políticas, la Data API
-- / clave anon NO puede leer ni escribir ninguna tabla de la app.
alter table users            enable row level security;
alter table services         enable row level security;
alter table service_packages enable row level security;
alter table bookings         enable row level security;
alter table chat_messages    enable row level security;
alter table salon_info       enable row level security;
alter table audit_logs       enable row level security;

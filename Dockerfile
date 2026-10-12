FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Create upload directory
RUN mkdir -p instance/uploads

# Expose port (Railway/Render inyectan $PORT; usamos 5000 en local)
EXPOSE 5000

ENV PYTHONUNBUFFERED=1
ENV TZ=America/Managua
# Producción por defecto: si alguien olvida la variable en Railway,
# la app queda en modo seguro (cookies Secure, validate_production)
# en vez de caer en la configuración de desarrollo.
ENV FLASK_ENV=production

# Run gunicorn (worker gthread = coherente con SocketIO async_mode threading).
# El puerto ($PORT de la plataforma) lo lee Python desde gunicorn.conf.py:
# no hace falta expansión de shell, así funciona en Railway/Render/Procfile.
CMD ["gunicorn", "-c", "gunicorn.conf.py", "app:app"]

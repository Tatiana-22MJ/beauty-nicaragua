# =============================================================================
# tests/test_validators.py — Validaciones server-side
# =============================================================================

import io

from validators import (
    parse_float,
    parse_int,
    validate_date,
    validate_email,
    validate_file_signature,
    validate_name,
    validate_password,
    validate_phone,
    validate_time,
    validate_username,
)


class TestValidateName:
    def test_nombre_valido(self):
        assert validate_name("María Auxiliadora") is None

    def test_muy_corto(self):
        assert validate_name("A") is not None

    def test_vacio(self):
        assert validate_name("") is not None


class TestValidateEmail:
    def test_email_valido(self):
        assert validate_email("clienta@correo.com.ni") is None

    def test_email_invalido(self):
        assert validate_email("no-es-email") is not None

    def test_vacio(self):
        assert validate_email("") is not None


class TestValidatePhone:
    def test_telefono_nicaraguense(self):
        assert validate_phone("+505 8877 2117") is None

    def test_telefono_invalido(self):
        assert validate_phone("abc") is not None


class TestValidateUsername:
    def test_valido(self):
        assert validate_username("maria_perez") is None

    def test_caracteres_invalidos(self):
        assert validate_username("maria-perez!") is not None

    def test_muy_corto(self):
        assert validate_username("ab") is not None


class TestValidatePassword:
    def test_valida(self):
        assert validate_password("Clave1234", "Clave1234") is None

    def test_corta(self):
        assert validate_password("Ab1", "") is not None

    def test_sin_numeros(self):
        assert validate_password("sololetras", "") is not None

    def test_no_coincide(self):
        assert validate_password("Clave1234", "Clave4321") is not None


class TestValidateDate:
    def test_fecha_pasada_rechazada(self):
        assert validate_date("2020-01-01") is not None

    def test_formato_invalido(self):
        assert validate_date("31/12/2026") is not None

    def test_vacia(self):
        assert validate_date("") is not None


class TestValidateTime:
    def test_valida(self):
        assert validate_time("09:30") is None

    def test_invalida(self):
        assert validate_time("9am") is not None


class TestParsers:
    def test_parse_float_valido(self):
        value, error = parse_float("1200.50", "precio")
        assert value == 1200.50
        assert error is None

    def test_parse_float_invalido(self):
        value, error = parse_float("abc", "precio")
        assert value is None
        assert error is not None

    def test_parse_float_negativo_rechazado(self):
        value, error = parse_float("-5", "precio")
        assert value is None
        assert error is not None

    def test_parse_int_valido(self):
        value, error = parse_int("90", "duración")
        assert value == 90
        assert error is None

    def test_parse_int_invalido(self):
        value, error = parse_int("90.5", "duración")
        assert value is None
        assert error is not None


class TestFileSignature:
    def test_png_real(self):
        png = io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"0" * 100)
        assert validate_file_signature(png, "comprobante.png") is None

    def test_pdf_real(self):
        pdf = io.BytesIO(b"%PDF-1.4 ...")
        assert validate_file_signature(pdf, "comprobante.pdf") is None

    def test_webp_real(self):
        webp = io.BytesIO(b"RIFF\x00\x00\x00\x00WEBPVP8 ")
        assert validate_file_signature(webp, "comprobante.webp") is None

    def test_ejecutable_renombrado_rechazado(self):
        exe = io.BytesIO(b"MZ\x90\x00" + b"0" * 100)
        assert validate_file_signature(exe, "comprobante.png") is not None

    def test_archivo_vacio_rechazado(self):
        empty = io.BytesIO(b"")
        assert validate_file_signature(empty, "comprobante.png") is not None

    def test_extension_no_permitida(self):
        png = io.BytesIO(b"\x89PNG\r\n\x1a\n")
        assert validate_file_signature(png, "script.sh") is not None

"""Pruebas de la lectura de configuración desde variables de entorno."""

import pytest

from config import Settings

VARIABLES = ["HOST", "PORT", "LOG_LEVEL", "APP_VERSION", "CARGAR_DATOS_EJEMPLO"]


@pytest.fixture(autouse=True)
def entorno_limpio(monkeypatch):
    for nombre in VARIABLES:
        monkeypatch.delenv(nombre, raising=False)


def test_valores_por_defecto():
    s = Settings.desde_entorno()
    assert s.host == "0.0.0.0"
    assert s.port == 8000
    assert s.log_level == "info"
    assert s.app_version == "1.0.0"
    assert s.cargar_datos_ejemplo is True


def test_valores_desde_el_entorno(monkeypatch):
    monkeypatch.setenv("HOST", "127.0.0.1")
    monkeypatch.setenv("PORT", "9000")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("APP_VERSION", "2.3.4")
    monkeypatch.setenv("CARGAR_DATOS_EJEMPLO", "false")
    s = Settings.desde_entorno()
    assert (s.host, s.port, s.log_level, s.app_version) == ("127.0.0.1", 9000, "debug", "2.3.4")
    assert s.cargar_datos_ejemplo is False


@pytest.mark.parametrize("variable, valor", [
    ("PORT", "abc"),
    ("PORT", "0"),
    ("PORT", "70000"),
    ("CARGAR_DATOS_EJEMPLO", "quizas"),
    ("LOG_LEVEL", "verbose"),
])
def test_valores_invalidos_fallan_al_arrancar(monkeypatch, variable, valor):
    monkeypatch.setenv(variable, valor)
    with pytest.raises(ValueError, match=variable):
        Settings.desde_entorno()

"""Configuración de la aplicación a partir de variables de entorno.

Siguiendo la metodología *12-factor*, la configuración no se escribe en el código:
se lee del entorno. Así la misma imagen Docker sirve para cualquier entorno
cambiando solo las variables, sin tocar el código.

Los valores por defecto reproducen el comportamiento original de la Práctica 2:
el servidor escucha en 0.0.0.0:8000 (accesible desde otros equipos de la red)
y al arrancar se cargan los datos de ejemplo de la Práctica 1.
"""

import os
from dataclasses import dataclass

_VERDADEROS = {"1", "true", "yes", "si", "sí", "on"}
_FALSOS = {"0", "false", "no", "off", ""}
_NIVELES_LOG = {"critical", "error", "warning", "info", "debug", "trace"}


def _leer_bool(nombre: str, por_defecto: bool) -> bool:
    valor = os.getenv(nombre)
    if valor is None:
        return por_defecto
    valor = valor.strip().lower()
    if valor in _VERDADEROS:
        return True
    if valor in _FALSOS:
        return False
    raise ValueError(f"La variable {nombre} debe ser true/false (valor recibido: '{valor}')")


def _leer_puerto(nombre: str, por_defecto: int) -> int:
    valor = os.getenv(nombre, str(por_defecto)).strip()
    if not valor.isdigit() or not 1 <= int(valor) <= 65535:
        raise ValueError(f"La variable {nombre} debe ser un puerto entre 1 y 65535 (valor: '{valor}')")
    return int(valor)


def _leer_nivel_log(nombre: str, por_defecto: str) -> str:
    valor = os.getenv(nombre, por_defecto).strip().lower()
    if valor not in _NIVELES_LOG:
        raise ValueError(f"La variable {nombre} debe ser uno de {sorted(_NIVELES_LOG)} (valor: '{valor}')")
    return valor


@dataclass(frozen=True)
class Settings:
    """Configuración inmutable del servidor."""

    host: str
    port: int
    log_level: str
    app_version: str
    cargar_datos_ejemplo: bool

    @classmethod
    def desde_entorno(cls) -> "Settings":
        return cls(
            host=os.getenv("HOST", "0.0.0.0").strip(),
            port=_leer_puerto("PORT", 8000),
            log_level=_leer_nivel_log("LOG_LEVEL", "info"),
            app_version=os.getenv("APP_VERSION", "1.0.0").strip(),
            cargar_datos_ejemplo=_leer_bool("CARGAR_DATOS_EJEMPLO", True),
        )


settings = Settings.desde_entorno()

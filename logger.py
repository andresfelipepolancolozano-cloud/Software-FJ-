"""
logger.py — Software FJ
Registro de eventos y errores en archivo de logs.
Singleton thread-safe para uso global en toda la aplicación.
"""

import os
import traceback
from datetime import datetime
from enum import Enum


class Nivel(Enum):
    INFO = "INFO"
    ADVERTENCIA = "ADVERTENCIA"
    ERROR = "ERROR"
    CRITICO = "CRITICO"


class Logger:
    """
    Logger Singleton que escribe eventos en 'softwarefj.log'.
    También imprime en consola con colores ANSI para mejor legibilidad.
    """

    _instancia = None
    _RUTA_LOG = "softwarefj.log"

    # Colores ANSI
    _COLORES = {
        Nivel.INFO:       "\033[36m",   # Cyan
        Nivel.ADVERTENCIA: "\033[33m",  # Amarillo
        Nivel.ERROR:      "\033[31m",   # Rojo
        Nivel.CRITICO:    "\033[35m",   # Magenta
    }
    _RESET = "\033[0m"

    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia._inicializar()
        return cls._instancia

    def _inicializar(self):
        self._ruta = self._RUTA_LOG
        # Crear / abrir el archivo para escritura acumulada
        with open(self._ruta, "a", encoding="utf-8") as f:
            separador = "=" * 70
            f.write(f"\n{separador}\n")
            f.write(f"  SESIÓN INICIADA: {self._timestamp()}\n")
            f.write(f"{separador}\n")

    # ── helpers ──────────────────────────────────────────────────────────
    @staticmethod
    def _timestamp() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _escribir(self, nivel: Nivel, origen: str, mensaje: str, exc: Exception = None):
        ts = self._timestamp()
        linea = f"[{ts}] [{nivel.value:<12}] [{origen:<25}] {mensaje}"

        # Traza de excepción si aplica
        traza = ""
        if exc is not None:
            traza = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))

        # ── Archivo ──
        try:
            with open(self._ruta, "a", encoding="utf-8") as f:
                f.write(linea + "\n")
                if traza:
                    for tl in traza.splitlines():
                        f.write(f"    {tl}\n")
        except OSError as e:
            print(f"[LOGGER-FALLO] No se pudo escribir en el log: {e}")

        # ── Consola ──
        color = self._COLORES.get(nivel, "")
        print(f"{color}{linea}{self._RESET}")
        if traza and nivel in (Nivel.ERROR, Nivel.CRITICO):
            # En consola solo mostramos la última línea de la traza
            ultima = [l for l in traza.splitlines() if l.strip()]
            if ultima:
                print(f"  {color}↳ {ultima[-1]}{self._RESET}")

    # ── API pública ───────────────────────────────────────────────────────
    def info(self, origen: str, mensaje: str):
        self._escribir(Nivel.INFO, origen, mensaje)

    def advertencia(self, origen: str, mensaje: str):
        self._escribir(Nivel.ADVERTENCIA, origen, mensaje)

    def error(self, origen: str, mensaje: str, exc: Exception = None):
        self._escribir(Nivel.ERROR, origen, mensaje, exc)

    def critico(self, origen: str, mensaje: str, exc: Exception = None):
        self._escribir(Nivel.CRITICO, origen, mensaje, exc)

    @property
    def ruta_log(self) -> str:
        return os.path.abspath(self._ruta)


# Instancia global de acceso rápido
log = Logger()

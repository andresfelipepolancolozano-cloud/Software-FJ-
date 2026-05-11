"""
entidad.py — Software FJ
Clase abstracta raíz que establece el contrato común para todas
las entidades del sistema (Cliente, Servicio, Reserva, etc.).
"""

from abc import ABC, abstractmethod
from datetime import datetime


class Entidad(ABC):
    """
    Clase abstracta base del sistema Software FJ.

    Define la interfaz mínima que toda entidad del dominio
    debe implementar: identificador único, fecha de creación,
    descripción textual y serialización resumida.

    Principios aplicados
    --------------------
    - Abstracción  : métodos abstractos obligan a las subclases a
                     implementar la lógica específica de cada entidad.
    - Encapsulación: los atributos se exponen sólo mediante propiedades.
    """

    def __init__(self, id_entidad: str):
        # Atributos privados: solo accesibles mediante las propiedades de abajo
        self.__id_entidad: str = id_entidad
        self.__fecha_creacion: datetime = datetime.now()

    # Propiedades de solo lectura — no tienen setter para proteger la integridad del objeto

    @property
    def id_entidad(self) -> str:
        # Identificador único de la entidad (no cambia después de crearse)
        return self.__id_entidad

    @property
    def fecha_creacion(self) -> datetime:
        # Fecha y hora exacta en que se instanció el objeto
        return self.__fecha_creacion

    @property
    def fecha_creacion_str(self) -> str:
        # Versión formateada de fecha_creacion, lista para mostrar en pantalla o logs
        return self.__fecha_creacion.strftime("%Y-%m-%d %H:%M:%S")

    # Métodos abstractos — cada subclase DEBE implementarlos

    @abstractmethod
    def describir(self) -> str:
        """Devuelve una descripción completa de la entidad."""

    @abstractmethod
    def resumen(self) -> str:
        """Devuelve una línea corta de identificación de la entidad."""

    @abstractmethod
    def validar(self) -> bool:
        """
        Valida la consistencia interna de la entidad.
        Devuelve True si es válida; lanza excepción si no lo es.
        """

    # Métodos concretos compartidos por todas las subclases

    def __repr__(self) -> str:
        # Representación técnica útil para depuración
        return f"<{self.__class__.__name__} id='{self.__id_entidad}'>"

    def __eq__(self, other: object) -> bool:
        # Dos entidades son iguales si tienen el mismo ID, independientemente del tipo
        if not isinstance(other, Entidad):
            return NotImplemented
        return self.__id_entidad == other.__id_entidad

    def __hash__(self) -> int:
        # Permite usar entidades como claves de diccionario o elementos de conjuntos
        return hash(self.__id_entidad)

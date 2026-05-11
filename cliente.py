"""
cliente.py — Software FJ
Clase Cliente con encapsulación estricta y validaciones robustas.
"""

import re
from entidad import Entidad
from excepciones import DatoClienteInvalidoError
from logger import log


class Cliente(Entidad):
    """
    Representa a un cliente de Software FJ.

    Encapsula datos personales sensibles (nombre, email, teléfono,
    identificación) y los expone solo mediante propiedades con
    setters que validan cada cambio.

    Principios aplicados
    --------------------
    - Herencia     : extiende la clase abstracta Entidad.
    - Encapsulación: atributos privados con doble guion bajo.
    - Polimorfismo : implementa describir(), resumen() y validar().
    """

    # Expresiones regulares reutilizables para validar los campos del cliente
    _RE_EMAIL    = re.compile(r"^[\w\.\+\-]+@[\w\-]+\.[a-zA-Z]{2,}$")
    _RE_TELEFONO = re.compile(r"^\+?[\d\s\-\(\)]{7,20}$")
    _RE_ID       = re.compile(r"^[A-Za-z0-9\-]{3,20}$")

    def __init__(
        self,
        identificacion: str,
        nombre: str,
        email: str,
        telefono: str,
        empresa: str = "",
    ):
        """
        Parameters
        ----------
        identificacion : str  — cédula / NIT / pasaporte (3-20 alfanuméricos)
        nombre         : str  — nombre completo (mín. 3 chars)
        email          : str  — correo electrónico válido
        telefono       : str  — teléfono con formato flexible
        empresa        : str  — razón social (opcional)
        """
        super().__init__(identificacion)

        # Se valida cada campo antes de asignarlo; si alguno falla lanza DatoClienteInvalidoError
        self._validar_identificacion(identificacion)
        self._validar_nombre(nombre)
        self._validar_email(email)
        self._validar_telefono(telefono)

        # Atributos privados — solo accesibles a través de las propiedades
        self.__identificacion: str      = identificacion.strip()
        self.__nombre: str              = nombre.strip()
        self.__email: str               = email.strip().lower()
        self.__telefono: str            = telefono.strip()
        self.__empresa: str             = empresa.strip()
        self.__activo: bool             = True   # Todo cliente inicia como activo
        self.__historial_reservas: list = []     # IDs de reservas asociadas al cliente

        log.info("Cliente", f"Cliente creado: {self.__nombre} ({self.__identificacion})")

    # Validaciones estáticas — se pueden llamar sin instanciar la clase

    @staticmethod
    def _validar_identificacion(valor: str):
        if not valor or not isinstance(valor, str):
            raise DatoClienteInvalidoError("identificacion", valor, "no puede ser vacío")
        if not Cliente._RE_ID.match(valor.strip()):
            raise DatoClienteInvalidoError(
                "identificacion", valor,
                "solo alfanuméricos y guiones, entre 3 y 20 caracteres"
            )

    @staticmethod
    def _validar_nombre(valor: str):
        if not valor or not isinstance(valor, str) or len(valor.strip()) < 3:
            raise DatoClienteInvalidoError("nombre", valor, "debe tener al menos 3 caracteres")

    @staticmethod
    def _validar_email(valor: str):
        if not valor or not isinstance(valor, str):
            raise DatoClienteInvalidoError("email", valor, "no puede ser vacío")
        if not Cliente._RE_EMAIL.match(valor.strip()):
            raise DatoClienteInvalidoError("email", valor, "formato de correo inválido")

    @staticmethod
    def _validar_telefono(valor: str):
        if not valor or not isinstance(valor, str):
            raise DatoClienteInvalidoError("telefono", valor, "no puede ser vacío")
        if not Cliente._RE_TELEFONO.match(valor.strip()):
            raise DatoClienteInvalidoError("telefono", valor, "formato de teléfono inválido")

    # Propiedades — getters de solo lectura; los setters validan antes de asignar

    @property
    def identificacion(self) -> str:
        return self.__identificacion

    @property
    def nombre(self) -> str:
        return self.__nombre

    @nombre.setter
    def nombre(self, valor: str):
        # Valida el nuevo nombre antes de reemplazar el actual
        self._validar_nombre(valor)
        self.__nombre = valor.strip()
        log.info("Cliente", f"Nombre actualizado para {self.__identificacion}: {self.__nombre}")

    @property
    def email(self) -> str:
        return self.__email

    @email.setter
    def email(self, valor: str):
        self._validar_email(valor)
        self.__email = valor.strip().lower()

    @property
    def telefono(self) -> str:
        return self.__telefono

    @telefono.setter
    def telefono(self, valor: str):
        self._validar_telefono(valor)
        self.__telefono = valor.strip()

    @property
    def empresa(self) -> str:
        return self.__empresa

    @property
    def activo(self) -> bool:
        return self.__activo

    @property
    def historial_reservas(self) -> list:
        # Devuelve una copia para que nadie pueda modificar la lista interna directamente
        return list(self.__historial_reservas)

    # Métodos de negocio

    def desactivar(self):
        """Marca al cliente como inactivo; no podrá hacer nuevas reservas."""
        self.__activo = False
        log.advertencia("Cliente", f"Cliente desactivado: {self.__nombre} ({self.__identificacion})")

    def activar(self):
        """Reactiva un cliente previamente desactivado."""
        self.__activo = True
        log.info("Cliente", f"Cliente reactivado: {self.__nombre} ({self.__identificacion})")

    def agregar_reserva(self, id_reserva: str):
        """Registra el ID de una reserva en el historial interno del cliente."""
        if id_reserva not in self.__historial_reservas:
            self.__historial_reservas.append(id_reserva)

    # Implementación del contrato de Entidad

    def describir(self) -> str:
        # Descripción completa con todos los datos del cliente
        estado = "Activo" if self.__activo else "Inactivo"
        empresa = f" | Empresa: {self.__empresa}" if self.__empresa else ""
        return (
            f"Cliente: {self.__nombre}\n"
            f"  ID     : {self.__identificacion}\n"
            f"  Email  : {self.__email}\n"
            f"  Tel    : {self.__telefono}{empresa}\n"
            f"  Estado : {estado}\n"
            f"  Reservas registradas: {len(self.__historial_reservas)}"
        )

    def resumen(self) -> str:
        # Una sola línea con la información mínima de identificación
        return f"Cliente({self.__identificacion}) — {self.__nombre}"

    def validar(self) -> bool:
        # Revalida todos los campos para confirmar que el objeto sigue siendo consistente
        try:
            self._validar_identificacion(self.__identificacion)
            self._validar_nombre(self.__nombre)
            self._validar_email(self.__email)
            self._validar_telefono(self.__telefono)
            return True
        except DatoClienteInvalidoError as e:
            raise DatoClienteInvalidoError("validacion_interna", "", str(e)) from e

    def __str__(self) -> str:
        return self.resumen()

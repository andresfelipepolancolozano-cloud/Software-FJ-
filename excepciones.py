"""
excepciones.py — Software FJ
Jerarquía completa de excepciones personalizadas del sistema.
"""


# ──────────────────────────────────────────────
#  Excepción raíz del sistema
# ──────────────────────────────────────────────
class SoftwareFJError(Exception):
    """Excepción base de la que heredan todas las del sistema."""

    def __init__(self, mensaje: str, codigo: str = "ERR_GENERICO"):
        super().__init__(mensaje)
        self.codigo = codigo
        self.mensaje = mensaje

    def __str__(self):
        return f"[{self.codigo}] {self.mensaje}"


# ──────────────────────────────────────────────
#  Excepciones de Cliente
# ──────────────────────────────────────────────
class ClienteError(SoftwareFJError):
    """Error base relacionado con operaciones de clientes."""


class ClienteYaExisteError(ClienteError):
    def __init__(self, identificacion: str):
        super().__init__(
            f"Ya existe un cliente con identificación '{identificacion}'.",
            "ERR_CLIENTE_DUPLICADO",
        )


class ClienteNoEncontradoError(ClienteError):
    def __init__(self, identificacion: str):
        super().__init__(
            f"No se encontró ningún cliente con identificación '{identificacion}'.",
            "ERR_CLIENTE_NO_ENCONTRADO",
        )


class DatoClienteInvalidoError(ClienteError):
    def __init__(self, campo: str, valor, motivo: str = ""):
        detalle = f" — {motivo}" if motivo else ""
        super().__init__(
            f"Dato inválido en campo '{campo}' con valor '{valor}'{detalle}.",
            "ERR_DATO_CLIENTE_INVALIDO",
        )


# ──────────────────────────────────────────────
#  Excepciones de Servicio
# ──────────────────────────────────────────────
class ServicioError(SoftwareFJError):
    """Error base relacionado con servicios."""


class ServicioNoDisponibleError(ServicioError):
    def __init__(self, nombre_servicio: str):
        super().__init__(
            f"El servicio '{nombre_servicio}' no está disponible en este momento.",
            "ERR_SERVICIO_NO_DISPONIBLE",
        )


class ParametroServicioInvalidoError(ServicioError):
    def __init__(self, parametro: str, valor, motivo: str = ""):
        detalle = f" — {motivo}" if motivo else ""
        super().__init__(
            f"Parámetro inválido '{parametro}' = '{valor}'{detalle}.",
            "ERR_PARAMETRO_INVALIDO",
        )


class CapacidadExcedidaError(ServicioError):
    def __init__(self, servicio: str, capacidad_max: int, solicitado: int):
        super().__init__(
            f"'{servicio}' tiene capacidad máxima {capacidad_max}; se solicitaron {solicitado}.",
            "ERR_CAPACIDAD_EXCEDIDA",
        )


class CalculoCostoError(ServicioError):
    def __init__(self, detalle: str):
        super().__init__(
            f"Error al calcular el costo del servicio: {detalle}.",
            "ERR_CALCULO_COSTO",
        )


# ──────────────────────────────────────────────
#  Excepciones de Reserva
# ──────────────────────────────────────────────
class ReservaError(SoftwareFJError):
    """Error base relacionado con reservas."""


class ReservaNoEncontradaError(ReservaError):
    def __init__(self, id_reserva: str):
        super().__init__(
            f"No se encontró la reserva con ID '{id_reserva}'.",
            "ERR_RESERVA_NO_ENCONTRADA",
        )


class ReservaYaCanceladaError(ReservaError):
    def __init__(self, id_reserva: str):
        super().__init__(
            f"La reserva '{id_reserva}' ya fue cancelada previamente.",
            "ERR_RESERVA_YA_CANCELADA",
        )


class ReservaYaConfirmadaError(ReservaError):
    def __init__(self, id_reserva: str):
        super().__init__(
            f"La reserva '{id_reserva}' ya se encuentra confirmada.",
            "ERR_RESERVA_YA_CONFIRMADA",
        )


class DuracionInvalidaError(ReservaError):
    def __init__(self, duracion):
        super().__init__(
            f"La duración '{duracion}' no es válida; debe ser un número positivo.",
            "ERR_DURACION_INVALIDA",
        )


class OperacionNoPermitidaError(SoftwareFJError):
    def __init__(self, operacion: str, motivo: str = ""):
        detalle = f": {motivo}" if motivo else ""
        super().__init__(
            f"Operación no permitida — '{operacion}'{detalle}.",
            "ERR_OPERACION_NO_PERMITIDA",
        )

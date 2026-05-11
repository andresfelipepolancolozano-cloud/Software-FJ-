"""
excepciones.py — Software FJ
Jerarquía completa de excepciones personalizadas del sistema.
"""


# Excepción raíz del sistema — todas las demás heredan de esta
class SoftwareFJError(Exception):
    """Excepción base de la que heredan todas las del sistema."""

    def __init__(self, mensaje: str, codigo: str = "ERR_GENERICO"):
        super().__init__(mensaje)
        self.codigo = codigo     # Código identificador del tipo de error
        self.mensaje = mensaje   # Mensaje legible del error

    def __str__(self):
        # Formato estándar: [CODIGO] mensaje
        return f"[{self.codigo}] {self.mensaje}"


# EXCEPCIONES DE CLIENTE

class ClienteError(SoftwareFJError):
    """Error base relacionado con operaciones de clientes."""


class ClienteYaExisteError(ClienteError):
    # Se lanza cuando se intenta registrar un cliente con una identificación que ya existe
    def __init__(self, identificacion: str):
        super().__init__(
            f"Ya existe un cliente con identificación '{identificacion}'.",
            "ERR_CLIENTE_DUPLICADO",
        )


class ClienteNoEncontradoError(ClienteError):
    # Se lanza cuando se busca un cliente que no está registrado en el sistema
    def __init__(self, identificacion: str):
        super().__init__(
            f"No se encontró ningún cliente con identificación '{identificacion}'.",
            "ERR_CLIENTE_NO_ENCONTRADO",
        )


class DatoClienteInvalidoError(ClienteError):
    # Se lanza cuando un campo del cliente no cumple las reglas de validación
    def __init__(self, campo: str, valor, motivo: str = ""):
        detalle = f" — {motivo}" if motivo else ""
        super().__init__(
            f"Dato inválido en campo '{campo}' con valor '{valor}'{detalle}.",
            "ERR_DATO_CLIENTE_INVALIDO",
        )


# EXCEPCIONES DE SERVICIO

class ServicioError(SoftwareFJError):
    """Error base relacionado con servicios."""


class ServicioNoDisponibleError(ServicioError):
    # Se lanza cuando se intenta usar un servicio que está deshabilitado
    def __init__(self, nombre_servicio: str):
        super().__init__(
            f"El servicio '{nombre_servicio}' no está disponible en este momento.",
            "ERR_SERVICIO_NO_DISPONIBLE",
        )


class ParametroServicioInvalidoError(ServicioError):
    # Se lanza cuando un parámetro enviado al servicio tiene un valor inválido
    def __init__(self, parametro: str, valor, motivo: str = ""):
        detalle = f" — {motivo}" if motivo else ""
        super().__init__(
            f"Parámetro inválido '{parametro}' = '{valor}'{detalle}.",
            "ERR_PARAMETRO_INVALIDO",
        )


class CapacidadExcedidaError(ServicioError):
    # Se lanza cuando se solicitan más personas o unidades de las que el servicio permite
    def __init__(self, servicio: str, capacidad_max: int, solicitado: int):
        super().__init__(
            f"'{servicio}' tiene capacidad máxima {capacidad_max}; se solicitaron {solicitado}.",
            "ERR_CAPACIDAD_EXCEDIDA",
        )


class CalculoCostoError(ServicioError):
    # Se lanza cuando el cálculo del costo produce un resultado inválido o falla
    def __init__(self, detalle: str):
        super().__init__(
            f"Error al calcular el costo del servicio: {detalle}.",
            "ERR_CALCULO_COSTO",
        )


# EXCEPCIONES DE RESERVA

class ReservaError(SoftwareFJError):
    """Error base relacionado con reservas."""


class ReservaNoEncontradaError(ReservaError):
    # Se lanza cuando se busca una reserva con un ID que no existe
    def __init__(self, id_reserva: str):
        super().__init__(
            f"No se encontró la reserva con ID '{id_reserva}'.",
            "ERR_RESERVA_NO_ENCONTRADA",
        )


class ReservaYaCanceladaError(ReservaError):
    # Se lanza cuando se intenta operar sobre una reserva que ya fue cancelada
    def __init__(self, id_reserva: str):
        super().__init__(
            f"La reserva '{id_reserva}' ya fue cancelada previamente.",
            "ERR_RESERVA_YA_CANCELADA",
        )


class ReservaYaConfirmadaError(ReservaError):
    # Se lanza cuando se intenta confirmar una reserva que ya estaba confirmada
    def __init__(self, id_reserva: str):
        super().__init__(
            f"La reserva '{id_reserva}' ya se encuentra confirmada.",
            "ERR_RESERVA_YA_CONFIRMADA",
        )


class DuracionInvalidaError(ReservaError):
    # Se lanza cuando la duración de una reserva no es un número positivo válido
    def __init__(self, duracion):
        super().__init__(
            f"La duración '{duracion}' no es válida; debe ser un número positivo.",
            "ERR_DURACION_INVALIDA",
        )


class OperacionNoPermitidaError(SoftwareFJError):
    # Se lanza cuando se intenta realizar una acción que no está permitida en el estado actual
    def __init__(self, operacion: str, motivo: str = ""):
        detalle = f": {motivo}" if motivo else ""
        super().__init__(
            f"Operación no permitida — '{operacion}'{detalle}.",
            "ERR_OPERACION_NO_PERMITIDA",
        )

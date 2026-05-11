"""
sistema.py — Software FJ
Clase GestorSistema: orquesta clientes, servicios y reservas.
Actúa como fachada (Facade) del sistema completo.
"""

from cliente import Cliente
from servicios import Servicio
from reserva import Reserva, EstadoReserva
from excepciones import (
    ClienteYaExisteError,
    ClienteNoEncontradoError,
    ReservaNoEncontradaError,
    OperacionNoPermitidaError,
    SoftwareFJError,
)
from logger import log


class GestorSistema:
    """
    Sistema central de Software FJ.

    Gestiona tres repositorios en memoria (sin base de datos):
      - __clientes  : dict[identificacion → Cliente]
      - __servicios : dict[id_servicio    → Servicio]
      - __reservas  : dict[id_reserva     → Reserva]

    Toda operación está protegida con manejo de excepciones y
    produce entradas en el archivo de log.
    """

    def __init__(self):
        self.__clientes:  dict[str, Cliente]  = {}
        self.__servicios: dict[str, Servicio] = {}
        self.__reservas:  dict[str, Reserva]  = {}
        log.info("GestorSistema", "Sistema Software FJ inicializado.")

    # ════════════════════════════════════════════════════════════════
    #  GESTIÓN DE CLIENTES
    # ════════════════════════════════════════════════════════════════

    def registrar_cliente(
        self,
        identificacion: str,
        nombre: str,
        email: str,
        telefono: str,
        empresa: str = "",
    ) -> Cliente:
        """Crea y almacena un cliente. Lanza excepción si ya existe."""
        try:
            if identificacion in self.__clientes:
                raise ClienteYaExisteError(identificacion)
            cliente = Cliente(identificacion, nombre, email, telefono, empresa)
            self.__clientes[identificacion] = cliente
        except ClienteYaExisteError as e:
            log.error("GestorSistema.registrar_cliente", str(e), e)
            raise
        except SoftwareFJError as e:
            log.error("GestorSistema.registrar_cliente", str(e), e)
            raise
        except Exception as e:
            log.critico("GestorSistema.registrar_cliente", f"Error inesperado: {e}", e)
            raise
        else:
            log.info("GestorSistema", f"Cliente registrado en sistema: {cliente.resumen()}")
            return cliente

    def obtener_cliente(self, identificacion: str) -> Cliente:
        try:
            if identificacion not in self.__clientes:
                raise ClienteNoEncontradoError(identificacion)
            return self.__clientes[identificacion]
        except ClienteNoEncontradoError as e:
            log.error("GestorSistema.obtener_cliente", str(e), e)
            raise

    def listar_clientes(self) -> list[Cliente]:
        return list(self.__clientes.values())

    def desactivar_cliente(self, identificacion: str) -> None:
        cliente = self.obtener_cliente(identificacion)
        cliente.desactivar()

    # ════════════════════════════════════════════════════════════════
    #  GESTIÓN DE SERVICIOS
    # ════════════════════════════════════════════════════════════════

    def registrar_servicio(self, servicio: Servicio) -> Servicio:
        """Almacena un servicio ya construido."""
        try:
            if not isinstance(servicio, Servicio):
                raise OperacionNoPermitidaError(
                    "registrar_servicio", "el objeto no es una instancia de Servicio"
                )
            servicio.validar()
            self.__servicios[servicio.id_entidad] = servicio
        except SoftwareFJError as e:
            log.error("GestorSistema.registrar_servicio", str(e), e)
            raise
        except Exception as e:
            log.critico("GestorSistema.registrar_servicio", f"Error inesperado: {e}", e)
            raise
        else:
            log.info("GestorSistema", f"Servicio registrado: {servicio.resumen()}")
            return servicio

    def obtener_servicio(self, id_servicio: str) -> Servicio:
        if id_servicio not in self.__servicios:
            from excepciones import ServicioNoDisponibleError
            raise ServicioNoDisponibleError(id_servicio)
        return self.__servicios[id_servicio]

    def listar_servicios(self) -> list[Servicio]:
        return list(self.__servicios.values())

    # ════════════════════════════════════════════════════════════════
    #  GESTIÓN DE RESERVAS
    # ════════════════════════════════════════════════════════════════

    def crear_reserva(
        self,
        id_cliente: str,
        id_servicio: str,
        horas: float,
        *,
        con_iva: bool = True,
        descuento: float = 0.0,
        notas: str = "",
        **kwargs_servicio,
    ) -> Reserva:
        """
        Crea una reserva vinculando cliente y servicio.
        Usa try/except/else/finally.
        """
        reserva = None
        try:
            cliente  = self.obtener_cliente(id_cliente)
            servicio = self.obtener_servicio(id_servicio)

            if not cliente.activo:
                raise OperacionNoPermitidaError(
                    "crear_reserva", f"el cliente '{cliente.nombre}' está inactivo"
                )

            reserva = Reserva(
                cliente, servicio, horas,
                con_iva=con_iva,
                descuento=descuento,
                notas=notas,
                **kwargs_servicio,
            )
            self.__reservas[reserva.id_reserva] = reserva

        except SoftwareFJError as e:
            log.error("GestorSistema.crear_reserva", str(e), e)
            raise
        except Exception as e:
            log.critico("GestorSistema.crear_reserva", f"Error inesperado: {e}", e)
            raise
        else:
            log.info("GestorSistema", f"Reserva almacenada: {reserva.resumen()}")
        finally:
            estado = reserva.estado.value if reserva else "FALLIDA"
            log.info(
                "GestorSistema.crear_reserva",
                f"Proceso de creación finalizado — estado={estado}"
            )

        return reserva

    def confirmar_reserva(self, id_reserva: str) -> None:
        reserva = self._obtener_reserva(id_reserva)
        reserva.confirmar()

    def cancelar_reserva(self, id_reserva: str, motivo: str = "") -> None:
        reserva = self._obtener_reserva(id_reserva)
        reserva.cancelar(motivo)

    def completar_reserva(self, id_reserva: str) -> None:
        reserva = self._obtener_reserva(id_reserva)
        reserva.completar()

    def _obtener_reserva(self, id_reserva: str) -> Reserva:
        if id_reserva not in self.__reservas:
            raise ReservaNoEncontradaError(id_reserva)
        return self.__reservas[id_reserva]

    def listar_reservas(
        self,
        estado: EstadoReserva | None = None,
        id_cliente: str | None = None,
    ) -> list[Reserva]:
        resultado = list(self.__reservas.values())
        if estado is not None:
            resultado = [r for r in resultado if r.estado == estado]
        if id_cliente is not None:
            resultado = [r for r in resultado if r.cliente.identificacion == id_cliente]
        return resultado

    # ════════════════════════════════════════════════════════════════
    #  REPORTES
    # ════════════════════════════════════════════════════════════════

    def reporte_resumen(self) -> str:
        total_reservas    = len(self.__reservas)
        confirmadas       = sum(1 for r in self.__reservas.values() if r.estado == EstadoReserva.CONFIRMADA)
        canceladas        = sum(1 for r in self.__reservas.values() if r.estado == EstadoReserva.CANCELADA)
        completadas       = sum(1 for r in self.__reservas.values() if r.estado == EstadoReserva.COMPLETADA)
        ingresos          = sum(
            r.costo for r in self.__reservas.values()
            if r.estado in (EstadoReserva.CONFIRMADA, EstadoReserva.COMPLETADA)
        )

        return (
            f"\n{'═'*55}\n"
            f"  REPORTE RESUMEN — SOFTWARE FJ\n"
            f"{'═'*55}\n"
            f"  Clientes registrados : {len(self.__clientes)}\n"
            f"  Servicios disponibles: {len(self.__servicios)}\n"
            f"  Total reservas       : {total_reservas}\n"
            f"    · Confirmadas      : {confirmadas}\n"
            f"    · Completadas      : {completadas}\n"
            f"    · Canceladas       : {canceladas}\n"
            f"    · Pendientes       : {total_reservas - confirmadas - canceladas - completadas}\n"
            f"  Ingresos proyectados : ${ingresos:,.2f}\n"
            f"{'═'*55}"
        )

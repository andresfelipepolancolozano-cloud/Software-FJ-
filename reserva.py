"""
reserva.py — Software FJ
Clase Reserva que integra Cliente + Servicio + ciclo de vida completo:
  PENDIENTE → CONFIRMADA → COMPLETADA
            ↘ CANCELADA
"""

import uuid
from datetime import datetime
from enum import Enum
from entidad import Entidad
from excepciones import (
    DuracionInvalidaError,
    ReservaYaCanceladaError,
    ReservaYaConfirmadaError,
    OperacionNoPermitidaError,
    CalculoCostoError,
)
from logger import log


class EstadoReserva(Enum):
    PENDIENTE   = "PENDIENTE"
    CONFIRMADA  = "CONFIRMADA"
    COMPLETADA  = "COMPLETADA"
    CANCELADA   = "CANCELADA"


class Reserva(Entidad):
    """
    Representa una reserva de servicio realizada por un cliente.

    Ciclo de vida
    -------------
    PENDIENTE → confirmar() → CONFIRMADA → completar() → COMPLETADA
    Cualquier estado → cancelar() → CANCELADA (excepto ya cancelada)

    Principios aplicados
    --------------------
    - Herencia     : extiende Entidad.
    - Encapsulación: estado y costo encapsulados; se cambian solo
                     mediante métodos de negocio.
    - Polimorfismo : describir() y resumen() implementados.
    - Excepciones  : try/except, try/except/else, try/except/finally,
                     excepciones encadenadas.
    """

    def __init__(
        self,
        cliente,            # instancia de Cliente
        servicio,           # instancia de Servicio
        horas: float,
        *,
        con_iva: bool = True,
        descuento: float = 0.0,
        notas: str = "",
        **kwargs_servicio,
    ):
        # Generar ID único para la reserva
        id_reserva = f"RSV-{uuid.uuid4().hex[:8].upper()}"
        super().__init__(id_reserva)

        # ── Validar duración ──────────────────────────────────────────────
        try:
            horas = float(horas)
            if horas <= 0:
                raise DuracionInvalidaError(horas)
        except (TypeError, ValueError) as e:
            raise DuracionInvalidaError(horas) from e

        # ── Validar parámetros del servicio ───────────────────────────────
        try:
            servicio.validar_parametros(horas, **kwargs_servicio)
        except Exception as e:
            log.error("Reserva", f"Parámetros inválidos al crear reserva: {e}", e)
            raise

        # ── Calcular costo ────────────────────────────────────────────────
        costo_calculado = None
        try:
            costo_calculado = servicio.calcular_costo(
                horas,
                con_iva=con_iva,
                descuento=descuento,
                **kwargs_servicio,
            )
        except CalculoCostoError as e:
            log.error("Reserva", f"Error al calcular costo en nueva reserva: {e}", e)
            raise
        except Exception as e:
            nuevo_error = CalculoCostoError(f"fallo inesperado: {e}")
            log.error("Reserva", str(nuevo_error), e)
            raise nuevo_error from e
        else:
            log.info("Reserva", f"Costo calculado exitosamente: ${costo_calculado:.2f}")
        finally:
            log.info("Reserva", f"Intento de creación para cliente {cliente.identificacion} finalizado.")

        # ── Asignar atributos ─────────────────────────────────────────────
        self.__cliente          = cliente
        self.__servicio         = servicio
        self.__horas: float     = horas
        self.__costo: float     = costo_calculado
        self.__estado           = EstadoReserva.PENDIENTE
        self.__con_iva: bool    = con_iva
        self.__descuento: float = descuento
        self.__notas: str       = notas.strip()
        self.__fecha_confirmacion: datetime | None = None
        self.__fecha_cancelacion:  datetime | None = None
        self.__motivo_cancelacion: str = ""
        self.__kwargs_servicio = kwargs_servicio

        # Registrar en el historial del cliente
        cliente.agregar_reserva(id_reserva)

        log.info(
            "Reserva",
            f"Reserva creada: {id_reserva} | {cliente.nombre} | "
            f"{servicio.nombre} | {horas}h | ${costo_calculado:.2f}"
        )

    # ── Propiedades ───────────────────────────────────────────────────────
    @property
    def id_reserva(self) -> str:
        return self.id_entidad

    @property
    def cliente(self):
        return self.__cliente

    @property
    def servicio(self):
        return self.__servicio

    @property
    def horas(self) -> float:
        return self.__horas

    @property
    def costo(self) -> float:
        return self.__costo

    @property
    def estado(self) -> EstadoReserva:
        return self.__estado

    @property
    def notas(self) -> str:
        return self.__notas

    # ── Métodos de negocio ────────────────────────────────────────────────
    def confirmar(self) -> None:
        """
        Cambia el estado de PENDIENTE → CONFIRMADA.
        Usa try/except/else para manejar errores de transición.
        """
        try:
            if self.__estado == EstadoReserva.CANCELADA:
                raise ReservaYaCanceladaError(self.id_reserva)
            if self.__estado == EstadoReserva.CONFIRMADA:
                raise ReservaYaConfirmadaError(self.id_reserva)
            if self.__estado == EstadoReserva.COMPLETADA:
                raise OperacionNoPermitidaError(
                    "confirmar", "la reserva ya fue completada"
                )
        except (ReservaYaCanceladaError, ReservaYaConfirmadaError, OperacionNoPermitidaError) as e:
            log.error("Reserva.confirmar", str(e), e)
            raise
        else:
            self.__estado = EstadoReserva.CONFIRMADA
            self.__fecha_confirmacion = datetime.now()
            log.info("Reserva.confirmar", f"Reserva confirmada: {self.id_reserva}")
        finally:
            log.info("Reserva.confirmar", f"Intento de confirmación para {self.id_reserva} finalizado.")

    def cancelar(self, motivo: str = "") -> None:
        """
        Cancela la reserva desde cualquier estado activo.
        Usa try/except/finally.
        """
        try:
            if self.__estado == EstadoReserva.CANCELADA:
                raise ReservaYaCanceladaError(self.id_reserva)
            if self.__estado == EstadoReserva.COMPLETADA:
                raise OperacionNoPermitidaError(
                    "cancelar", "no se puede cancelar una reserva ya completada"
                )
            self.__estado = EstadoReserva.CANCELADA
            self.__fecha_cancelacion = datetime.now()
            self.__motivo_cancelacion = motivo.strip()
        except (ReservaYaCanceladaError, OperacionNoPermitidaError) as e:
            log.error("Reserva.cancelar", str(e), e)
            raise
        except Exception as e:
            log.critico("Reserva.cancelar", f"Error inesperado al cancelar: {e}", e)
            raise
        finally:
            log.info("Reserva.cancelar", f"Intento de cancelación para {self.id_reserva} finalizado.")

        log.advertencia(
            "Reserva.cancelar",
            f"Reserva cancelada: {self.id_reserva}"
            + (f" — Motivo: {motivo}" if motivo else "")
        )

    def completar(self) -> None:
        """Marca la reserva como COMPLETADA (solo desde CONFIRMADA)."""
        try:
            if self.__estado != EstadoReserva.CONFIRMADA:
                raise OperacionNoPermitidaError(
                    "completar",
                    f"estado actual '{self.__estado.value}' no permite completar"
                )
        except OperacionNoPermitidaError as e:
            log.error("Reserva.completar", str(e), e)
            raise
        else:
            self.__estado = EstadoReserva.COMPLETADA
            log.info("Reserva.completar", f"Reserva completada: {self.id_reserva}")

    def recalcular_costo(self, nuevo_descuento: float = None) -> float:
        """
        Recalcula el costo, opcionalmente con un nuevo descuento.
        Encadenamiento de excepciones si el recálculo falla.
        """
        try:
            if self.__estado in (EstadoReserva.CANCELADA, EstadoReserva.COMPLETADA):
                raise OperacionNoPermitidaError(
                    "recalcular_costo",
                    f"no permitido en estado '{self.__estado.value}'"
                )
            desc = nuevo_descuento if nuevo_descuento is not None else self.__descuento
            nuevo_costo = self.__servicio.calcular_costo(
                self.__horas,
                con_iva=self.__con_iva,
                descuento=desc,
                **self.__kwargs_servicio,
            )
            self.__costo = nuevo_costo
            if nuevo_descuento is not None:
                self.__descuento = nuevo_descuento
            log.info("Reserva.recalcular", f"Costo recalculado: ${self.__costo:.2f}")
            return self.__costo
        except CalculoCostoError as e:
            raise OperacionNoPermitidaError("recalcular_costo", str(e)) from e

    # ── Contrato Entidad ──────────────────────────────────────────────────
    def describir(self) -> str:
        conf = self.__fecha_confirmacion.strftime("%Y-%m-%d %H:%M") if self.__fecha_confirmacion else "—"
        canc = self.__fecha_cancelacion.strftime("%Y-%m-%d %H:%M")  if self.__fecha_cancelacion  else "—"
        desc_str = f"{self.__descuento*100:.0f}%" if self.__descuento > 0 else "Sin descuento"
        return (
            f"Reserva: {self.id_reserva}\n"
            f"  Cliente    : {self.__cliente.resumen()}\n"
            f"  Servicio   : {self.__servicio.resumen()}\n"
            f"  Duración   : {self.__horas} hora(s)\n"
            f"  Costo total: ${self.__costo:,.2f} {'(c/IVA)' if self.__con_iva else '(s/IVA)'}\n"
            f"  Descuento  : {desc_str}\n"
            f"  Estado     : {self.__estado.value}\n"
            f"  Creada     : {self.fecha_creacion_str}\n"
            f"  Confirmada : {conf}\n"
            f"  Cancelada  : {canc}"
            + (f"\n  Motivo     : {self.__motivo_cancelacion}" if self.__motivo_cancelacion else "")
            + (f"\n  Notas      : {self.__notas}" if self.__notas else "")
        )

    def resumen(self) -> str:
        return (
            f"Reserva({self.id_reserva}) | {self.__cliente.nombre} | "
            f"{self.__servicio.nombre} | {self.__horas}h | "
            f"${self.__costo:,.2f} | {self.__estado.value}"
        )

    def validar(self) -> bool:
        if self.__costo < 0:
            raise CalculoCostoError(f"costo negativo: {self.__costo}")
        return True

    def __str__(self) -> str:
        return self.resumen()

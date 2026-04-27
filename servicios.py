"""
servicios.py — Software FJ
Clase abstracta Servicio y tres implementaciones concretas:
  · ReservaSala       (reserva de salas de reuniones)
  · AlquilerEquipo    (alquiler de equipos tecnológicos)
  · Asesoria          (asesorías especializadas)

Demuestra herencia, polimorfismo y métodos sobrecargados
mediante parámetros opcionales para el cálculo de costos.
"""

from abc import abstractmethod
from entidad import Entidad
from excepciones import (
    ParametroServicioInvalidoError,
    ServicioNoDisponibleError,
    CapacidadExcedidaError,
    CalculoCostoError,
)
from logger import log


# ══════════════════════════════════════════════════════════════════════════
#  CLASE ABSTRACTA BASE — Servicio
# ══════════════════════════════════════════════════════════════════════════
class Servicio(Entidad):
    """
    Clase abstracta que representa cualquier servicio de Software FJ.

    Obliga a las subclases a implementar:
      - calcular_costo()  : precio base según duración
      - describir()       : descripción completa del servicio
      - validar_parametros(): verificación de parámetros específicos

    Provee implementaciones comunes de resumen() y validar().
    """

    IVA_DEFAULT = 0.19  # 19 %

    def __init__(self, id_servicio: str, nombre: str, precio_hora: float, disponible: bool = True):
        if not nombre or not isinstance(nombre, str) or len(nombre.strip()) < 3:
            raise ParametroServicioInvalidoError("nombre", nombre, "debe tener al menos 3 caracteres")
        if not isinstance(precio_hora, (int, float)) or precio_hora <= 0:
            raise ParametroServicioInvalidoError("precio_hora", precio_hora, "debe ser un número positivo")

        super().__init__(id_servicio)
        self.__nombre: str           = nombre.strip()
        self.__precio_hora: float    = float(precio_hora)
        self.__disponible: bool      = disponible

        log.info("Servicio", f"Servicio registrado: [{id_servicio}] {nombre} — ${precio_hora:.2f}/h")

    # ── Propiedades ───────────────────────────────────────────────────────
    @property
    def nombre(self) -> str:
        return self.__nombre

    @property
    def precio_hora(self) -> float:
        return self.__precio_hora

    @precio_hora.setter
    def precio_hora(self, valor: float):
        if not isinstance(valor, (int, float)) or valor <= 0:
            raise ParametroServicioInvalidoError("precio_hora", valor, "debe ser un número positivo")
        self.__precio_hora = float(valor)

    @property
    def disponible(self) -> bool:
        return self.__disponible

    def habilitar(self):
        self.__disponible = True
        log.info("Servicio", f"Servicio habilitado: {self.__nombre}")

    def deshabilitar(self):
        self.__disponible = False
        log.advertencia("Servicio", f"Servicio deshabilitado: {self.__nombre}")

    def verificar_disponibilidad(self):
        """Lanza ServicioNoDisponibleError si el servicio está inactivo."""
        if not self.__disponible:
            raise ServicioNoDisponibleError(self.__nombre)

    # ── Métodos abstractos (polimorfismo) ─────────────────────────────────
    @abstractmethod
    def calcular_costo(self, horas: float, *, con_iva: bool = True,
                       descuento: float = 0.0, **kwargs) -> float:
        """
        Calcula el costo total del servicio.

        Parameters
        ----------
        horas     : duración en horas
        con_iva   : si True aplica IVA (19 %)
        descuento : porcentaje de descuento en [0, 1]
        **kwargs  : parámetros adicionales específicos del servicio
        """

    @abstractmethod
    def validar_parametros(self, horas: float, **kwargs) -> bool:
        """Valida los parámetros propios del servicio antes de reservar."""

    # ── Métodos concretos comunes ─────────────────────────────────────────
    def _base_costo(self, horas: float, *, con_iva: bool = True, descuento: float = 0.0) -> float:
        """Calcula precio base × horas, aplica descuento e IVA."""
        try:
            if not isinstance(horas, (int, float)) or horas <= 0:
                raise CalculoCostoError(f"horas='{horas}' debe ser un número positivo")
            if not (0.0 <= descuento <= 1.0):
                raise CalculoCostoError(f"descuento='{descuento}' debe estar en [0, 1]")

            subtotal = self.__precio_hora * horas
            subtotal_con_descuento = subtotal * (1 - descuento)
            total = subtotal_con_descuento * (1 + self.IVA_DEFAULT) if con_iva else subtotal_con_descuento
            return round(total, 2)

        except CalculoCostoError:
            raise
        except Exception as e:
            raise CalculoCostoError(str(e)) from e

    def resumen(self) -> str:
        estado = "✓ Disponible" if self.__disponible else "✗ No disponible"
        return f"Servicio({self.id_entidad}) — {self.__nombre} | ${self.__precio_hora:.2f}/h | {estado}"

    def validar(self) -> bool:
        if not self.__nombre:
            raise ParametroServicioInvalidoError("nombre", self.__nombre, "vacío")
        if self.__precio_hora <= 0:
            raise ParametroServicioInvalidoError("precio_hora", self.__precio_hora, "debe ser positivo")
        return True

    def __str__(self) -> str:
        return self.resumen()


# ══════════════════════════════════════════════════════════════════════════
#  SERVICIO 1 — ReservaSala
# ══════════════════════════════════════════════════════════════════════════
class ReservaSala(Servicio):
    """
    Reserva de salas de reuniones / conferencias.

    Parámetros adicionales
    ----------------------
    capacidad_max : int   — número máximo de personas
    tiene_proyector: bool — si la sala tiene proyector incluido
    """

    COSTO_PROYECTOR_HORA = 15_000.0   # Costo adicional si se requiere proyector

    def __init__(
        self,
        id_servicio: str,
        nombre: str,
        precio_hora: float,
        capacidad_max: int,
        tiene_proyector: bool = False,
    ):
        if not isinstance(capacidad_max, int) or capacidad_max < 1:
            raise ParametroServicioInvalidoError(
                "capacidad_max", capacidad_max, "debe ser un entero positivo"
            )
        super().__init__(id_servicio, nombre, precio_hora)
        self.__capacidad_max: int       = capacidad_max
        self.__tiene_proyector: bool    = tiene_proyector

    @property
    def capacidad_max(self) -> int:
        return self.__capacidad_max

    @property
    def tiene_proyector(self) -> bool:
        return self.__tiene_proyector

    # ── Polimorfismo ──────────────────────────────────────────────────────
    def calcular_costo(
        self,
        horas: float,
        *,
        con_iva: bool = True,
        descuento: float = 0.0,
        num_personas: int = 1,
        usar_proyector: bool = False,
        **kwargs,
    ) -> float:
        """
        Sobrecarga conceptual mediante kwargs:
          - usar_proyector : agrega tarifa adicional por hora
          - num_personas   : valida capacidad antes de calcular
        """
        self.validar_parametros(horas, num_personas=num_personas, usar_proyector=usar_proyector)
        costo = self._base_costo(horas, con_iva=con_iva, descuento=descuento)

        if usar_proyector and self.__tiene_proyector:
            extra = self.COSTO_PROYECTOR_HORA * horas
            if con_iva:
                extra *= (1 + self.IVA_DEFAULT)
            costo += round(extra, 2)

        log.info("ReservaSala", f"Costo calculado: ${costo:.2f} | {horas}h | personas={num_personas}")
        return costo

    def validar_parametros(self, horas: float, *, num_personas: int = 1, usar_proyector: bool = False, **kwargs) -> bool:
        self.verificar_disponibilidad()
        if not isinstance(horas, (int, float)) or horas <= 0:
            raise ParametroServicioInvalidoError("horas", horas, "debe ser positivo")
        if not isinstance(num_personas, int) or num_personas < 1:
            raise ParametroServicioInvalidoError("num_personas", num_personas, "debe ser entero positivo")
        if num_personas > self.__capacidad_max:
            raise CapacidadExcedidaError(self.nombre, self.__capacidad_max, num_personas)
        if usar_proyector and not self.__tiene_proyector:
            raise ParametroServicioInvalidoError("usar_proyector", True, "esta sala no tiene proyector")
        return True

    def describir(self) -> str:
        proyector = "Sí" if self.__tiene_proyector else "No"
        return (
            f"[SALA] {self.nombre}\n"
            f"  ID          : {self.id_entidad}\n"
            f"  Precio/hora : ${self.precio_hora:,.2f}\n"
            f"  Capacidad   : {self.__capacidad_max} personas\n"
            f"  Proyector   : {proyector}\n"
            f"  Disponible  : {'Sí' if self.disponible else 'No'}"
        )


# ══════════════════════════════════════════════════════════════════════════
#  SERVICIO 2 — AlquilerEquipo
# ══════════════════════════════════════════════════════════════════════════
class AlquilerEquipo(Servicio):
    """
    Alquiler de equipos tecnológicos (laptops, proyectores portátiles, etc.).

    Parámetros adicionales
    ----------------------
    tipo_equipo    : str  — descripción del equipo
    stock_disponible: int — unidades en inventario
    """

    def __init__(
        self,
        id_servicio: str,
        nombre: str,
        precio_hora: float,
        tipo_equipo: str,
        stock_disponible: int = 1,
    ):
        if not tipo_equipo or not isinstance(tipo_equipo, str):
            raise ParametroServicioInvalidoError("tipo_equipo", tipo_equipo, "no puede estar vacío")
        if not isinstance(stock_disponible, int) or stock_disponible < 0:
            raise ParametroServicioInvalidoError(
                "stock_disponible", stock_disponible, "debe ser un entero no negativo"
            )
        super().__init__(id_servicio, nombre, precio_hora)
        self.__tipo_equipo: str         = tipo_equipo.strip()
        self.__stock_disponible: int    = stock_disponible

    @property
    def tipo_equipo(self) -> str:
        return self.__tipo_equipo

    @property
    def stock_disponible(self) -> int:
        return self.__stock_disponible

    def reducir_stock(self, cantidad: int = 1):
        if cantidad > self.__stock_disponible:
            raise CapacidadExcedidaError(self.nombre, self.__stock_disponible, cantidad)
        self.__stock_disponible -= cantidad
        if self.__stock_disponible == 0:
            self.deshabilitar()

    def reponer_stock(self, cantidad: int = 1):
        if not isinstance(cantidad, int) or cantidad < 1:
            raise ParametroServicioInvalidoError("cantidad", cantidad, "debe ser entero positivo")
        self.__stock_disponible += cantidad
        if not self.disponible:
            self.habilitar()

    # ── Polimorfismo ──────────────────────────────────────────────────────
    def calcular_costo(
        self,
        horas: float,
        *,
        con_iva: bool = True,
        descuento: float = 0.0,
        cantidad_unidades: int = 1,
        seguro: bool = False,
        **kwargs,
    ) -> float:
        """
        Variantes (sobrecarga conceptual):
          - cantidad_unidades : multiplica el precio base
          - seguro            : agrega 5 % del subtotal como tarifa de seguro
        """
        self.validar_parametros(horas, cantidad_unidades=cantidad_unidades)
        costo = self._base_costo(horas, con_iva=con_iva, descuento=descuento) * cantidad_unidades

        if seguro:
            tarifa_seguro = costo * 0.05
            costo += round(tarifa_seguro, 2)

        log.info("AlquilerEquipo", f"Costo calculado: ${costo:.2f} | {horas}h | uds={cantidad_unidades}")
        return round(costo, 2)

    def validar_parametros(self, horas: float, *, cantidad_unidades: int = 1, **kwargs) -> bool:
        self.verificar_disponibilidad()
        if not isinstance(horas, (int, float)) or horas <= 0:
            raise ParametroServicioInvalidoError("horas", horas, "debe ser positivo")
        if not isinstance(cantidad_unidades, int) or cantidad_unidades < 1:
            raise ParametroServicioInvalidoError("cantidad_unidades", cantidad_unidades, "debe ser entero positivo")
        if cantidad_unidades > self.__stock_disponible:
            raise CapacidadExcedidaError(self.nombre, self.__stock_disponible, cantidad_unidades)
        return True

    def describir(self) -> str:
        return (
            f"[EQUIPO] {self.nombre}\n"
            f"  ID          : {self.id_entidad}\n"
            f"  Tipo        : {self.__tipo_equipo}\n"
            f"  Precio/hora : ${self.precio_hora:,.2f}\n"
            f"  Stock       : {self.__stock_disponible} unidades\n"
            f"  Disponible  : {'Sí' if self.disponible else 'No'}"
        )


# ══════════════════════════════════════════════════════════════════════════
#  SERVICIO 3 — Asesoria
# ══════════════════════════════════════════════════════════════════════════
class Asesoria(Servicio):
    """
    Asesoría especializada (legal, contable, tecnológica, etc.).

    Parámetros adicionales
    ----------------------
    especialidad : str   — área de la asesoría
    nivel        : str   — 'basico' | 'intermedio' | 'experto'
    """

    MULTIPLICADORES_NIVEL = {
        "basico":      1.0,
        "intermedio":  1.3,
        "experto":     1.7,
    }

    def __init__(
        self,
        id_servicio: str,
        nombre: str,
        precio_hora: float,
        especialidad: str,
        nivel: str = "basico",
    ):
        nivel = nivel.lower().strip()
        if nivel not in Asesoria.MULTIPLICADORES_NIVEL:
            raise ParametroServicioInvalidoError(
                "nivel", nivel,
                f"debe ser uno de {list(Asesoria.MULTIPLICADORES_NIVEL.keys())}"
            )
        if not especialidad or not isinstance(especialidad, str):
            raise ParametroServicioInvalidoError("especialidad", especialidad, "no puede estar vacío")

        super().__init__(id_servicio, nombre, precio_hora)
        self.__especialidad: str = especialidad.strip()
        self.__nivel: str        = nivel

    @property
    def especialidad(self) -> str:
        return self.__especialidad

    @property
    def nivel(self) -> str:
        return self.__nivel

    # ── Polimorfismo ──────────────────────────────────────────────────────
    def calcular_costo(
        self,
        horas: float,
        *,
        con_iva: bool = True,
        descuento: float = 0.0,
        nivel_override: str = None,
        incluir_informe: bool = False,
        **kwargs,
    ) -> float:
        """
        Variantes (sobrecarga conceptual):
          - nivel_override  : usa un nivel distinto al configurado
          - incluir_informe : agrega $50.000 fijo por entrega de informe
        """
        nivel_efectivo = (nivel_override or self.__nivel).lower()
        if nivel_efectivo not in self.MULTIPLICADORES_NIVEL:
            raise ParametroServicioInvalidoError(
                "nivel_override", nivel_efectivo,
                f"debe ser uno de {list(self.MULTIPLICADORES_NIVEL.keys())}"
            )
        self.validar_parametros(horas)

        multiplicador = self.MULTIPLICADORES_NIVEL[nivel_efectivo]
        costo = self._base_costo(horas, con_iva=con_iva, descuento=descuento) * multiplicador

        if incluir_informe:
            extra_informe = 50_000.0
            if con_iva:
                extra_informe *= (1 + self.IVA_DEFAULT)
            costo += round(extra_informe, 2)

        log.info("Asesoria", f"Costo calculado: ${costo:.2f} | {horas}h | nivel={nivel_efectivo}")
        return round(costo, 2)

    def validar_parametros(self, horas: float, **kwargs) -> bool:
        self.verificar_disponibilidad()
        if not isinstance(horas, (int, float)) or horas <= 0:
            raise ParametroServicioInvalidoError("horas", horas, "debe ser positivo")
        if horas > 8:
            raise ParametroServicioInvalidoError(
                "horas", horas, "una asesoría no puede superar 8 horas continuas"
            )
        return True

    def describir(self) -> str:
        mult = self.MULTIPLICADORES_NIVEL[self.__nivel]
        return (
            f"[ASESORÍA] {self.nombre}\n"
            f"  ID            : {self.id_entidad}\n"
            f"  Especialidad  : {self.__especialidad}\n"
            f"  Nivel         : {self.__nivel} (×{mult})\n"
            f"  Precio/hora   : ${self.precio_hora:,.2f}\n"
            f"  Precio efectivo: ${self.precio_hora * mult:,.2f}\n"
            f"  Disponible    : {'Sí' if self.disponible else 'No'}"
        )

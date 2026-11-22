"""Entidades, validaciones y reglas de precios de Software FJ."""
import re
from abc import ABC, abstractmethod
from decimal import Decimal, DecimalException, ROUND_HALF_UP


class ErrorGestion(Exception):
    """Error controlable que la interfaz comunica y registra."""


class DatoInvalido(ErrorGestion):
    """Un dato obligatorio está ausente o fuera de los límites."""


class OperacionInvalida(ErrorGestion):
    """La operación contradice el estado del sistema."""


def texto(valor, campo):
    """Normaliza espacios y rechaza campos vacíos."""
    if not isinstance(valor, str) or not valor.strip():
        raise DatoInvalido(f"Falta {campo}.")
    return valor.strip()


def numero(valor, campo, minimo, maximo):
    """Convierte a decimal y conserva la causa de los errores de conversión."""
    try:
        resultado = Decimal(str(valor))
    except (DecimalException, ValueError) as causa:
        raise DatoInvalido(f"{campo} requiere un valor numérico.") from causa
    if not resultado.is_finite() or not minimo <= resultado <= maximo:
        raise DatoInvalido(f"{campo} debe estar entre {minimo} y {maximo}.")
    return resultado


class Entidad(ABC):
    """Identidad de solo lectura para los objetos del sistema."""
    def __init__(self, codigo):
        self.__codigo = texto(codigo, "el código").upper()

    @property
    def codigo(self):
        return self.__codigo

    @abstractmethod
    def describir(self):
        """Devuelve una descripción legible."""


class Cliente(Entidad):
    def __init__(self, codigo, nombre, correo):
        super().__init__(codigo)
        self.__nombre = texto(nombre, "el nombre")
        self.__correo = texto(correo, "el correo")
        if not re.fullmatch(r"[^\s@]+@[^\s@.]+(?:\.[^\s@.]+)+", self.__correo):
            raise DatoInvalido("El correo requiere usuario y dominio.")

    @property
    def correo(self):
        return self.__correo

    def describir(self):
        return f"{self.codigo} · {self.__nombre}"


class Servicio(Entidad):
    """Tarifa en pesos por hora. Cada especialidad define duración y precio."""
    def __init__(self, codigo, tarifa):
        super().__init__(codigo)
        self._tarifa = numero(tarifa, "La tarifa", Decimal("0.01"), 100000000)

    @abstractmethod
    def validar(self, horas):
        """Devuelve la duración admitida por esta especialidad."""

    @abstractmethod
    def subtotal(self, horas):
        """Calcula el costo antes de ajustes sobre una duración validada."""

    def calcular_costo(self, horas, *, descuento=0, impuesto=0):
        """Variantes por argumentos opcionales; primero descuento y luego impuesto."""
        base = self.subtotal(self.validar(horas))
        rebaja = numero(descuento, "El descuento (%)", 0, 100)
        tasa = numero(impuesto, "El impuesto (%)", 0, 100)
        return (base * (1 - rebaja / 100) * (1 + tasa / 100)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP)


def horas_enteras(horas, limite):
    cantidad = numero(horas, "La duración en horas", 1, limite)
    if cantidad != cantidad.to_integral_value():
        raise DatoInvalido("La duración debe expresarse en horas enteras.")
    return int(cantidad)


class Sala(Servicio):
    def validar(self, horas):
        return horas_enteras(horas, 8)

    def subtotal(self, horas):
        return self._tarifa * horas

    def describir(self):
        return f"{self.codigo} · sala por hora"


class Equipo(Servicio):
    def validar(self, horas):
        return horas_enteras(horas, 24)

    def subtotal(self, horas):
        # Cada alquiler incluye un cargo fijo de preparación.
        return self._tarifa * horas + 5000

    def describir(self):
        return f"{self.codigo} · equipo con preparación"


class Asesoria(Servicio):
    def validar(self, horas):
        return horas_enteras(horas, 4)

    def subtotal(self, horas):
        # La primera hora se cobra completa, las siguientes al 80 %.
        return self._tarifa * (1 + (horas - 1) * Decimal("0.80"))

    def describir(self):
        return f"{self.codigo} · asesoría especializada"


class Reserva(Entidad):
    def __init__(self, codigo, cliente, servicio, horas):
        super().__init__(codigo)
        self.__cliente = cliente
        self.__servicio = servicio
        self.__horas = servicio.validar(horas)
        self.__estado = "pendiente"

    @property
    def cliente(self):
        return self.__cliente

    @property
    def servicio(self):
        return self.__servicio

    @property
    def estado(self):
        return self.__estado

    def confirmar(self):
        if self.estado != "pendiente":
            raise OperacionInvalida("Solo se confirma una reserva pendiente.")
        self.__estado = "confirmada"

    def cancelar(self):
        if self.estado not in ("pendiente", "confirmada"):
            raise OperacionInvalida("La reserva ya está cerrada.")
        self.__estado = "cancelada"

    def procesar(self, **ajustes):
        if self.estado != "confirmada":
            raise OperacionInvalida("Primero debe confirmar la reserva.")
        # Calcular antes de cerrar permite corregir un porcentaje y reintentar.
        total = self.servicio.calcular_costo(self.__horas, **ajustes)
        self.__estado = "procesada"
        return total

    def describir(self):
        return f"{self.codigo} · {self.__cliente.codigo} · {self.servicio.codigo} · {self.estado}"

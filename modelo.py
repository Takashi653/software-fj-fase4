"""Entidades, validaciones y reglas de precios de Software FJ."""
# Las expresiones regulares validan el correo completo.
import re
# ABC y abstractmethod hacen obligatorio el contrato de las subclases.
from abc import ABC, abstractmethod
# Decimal evita aproximaciones binarias al calcular importes en pesos.
from decimal import Decimal, DecimalException, ROUND_HALF_UP


class ErrorGestion(Exception):
    """Error controlable que la interfaz comunica y registra."""


class DatoInvalido(ErrorGestion):
    """Un dato obligatorio está ausente o fuera de los límites."""


class OperacionInvalida(ErrorGestion):
    """La operación contradice el estado del sistema."""


def texto(valor, campo):
    """Normaliza espacios y rechaza campos vacíos."""
    # Un campo formado solo por espacios también se considera vacío.
    if not isinstance(valor, str) or not valor.strip():
        raise DatoInvalido(f"Falta {campo}.")
    # El valor normalizado es el que se conservará en el objeto.
    return valor.strip()


def numero(valor, campo, minimo, maximo):
    """Convierte a decimal y conserva la causa de los errores de conversión."""
    try:
        # Convertir primero a texto conserva la representación decimal de entrada.
        resultado = Decimal(str(valor))
    except (DecimalException, ValueError) as causa:
        # La causa original queda disponible para el traceback de la bitácora.
        raise DatoInvalido(f"{campo} requiere un valor numérico.") from causa
    # Se excluyen infinito y NaN antes de comparar los límites permitidos.
    if not resultado.is_finite() or not minimo <= resultado <= maximo:
        raise DatoInvalido(f"{campo} debe estar entre {minimo} y {maximo}.")
    return resultado


class Entidad(ABC):
    """Identidad de solo lectura para los objetos del sistema."""
    def __init__(self, codigo):
        # La misma clave identifica a «c1» y «C1» en todas las búsquedas.
        self.__codigo = texto(codigo, "el código").upper()

    # La propiedad permite consultar el código sin ofrecer un setter.
    @property
    def codigo(self):
        return self.__codigo

    # Cada entidad concreta debe proporcionar su propia descripción.
    @abstractmethod
    def describir(self):
        """Devuelve una descripción legible."""


class Cliente(Entidad):
    def __init__(self, codigo, nombre, correo):
        # El constructor común valida la clave antes de guardar los datos personales.
        super().__init__(codigo)
        self.__nombre = texto(nombre, "el nombre")
        self.__correo = texto(correo, "el correo")
        # Se exige una sola arroba y un dominio con al menos dos componentes.
        if not re.fullmatch(r"[^\s@]+@[^\s@.]+(?:\.[^\s@.]+)+", self.__correo):
            raise DatoInvalido("El correo requiere usuario y dominio.")

    # El correo se expone para consulta y se valida al crear el cliente.
    @property
    def correo(self):
        return self.__correo

    def describir(self):
        # El nombre identifica al cliente en el resumen de la operación.
        return f"{self.codigo} · {self.__nombre}"


class Servicio(Entidad):
    """Tarifa en pesos por hora. Cada especialidad define duración y precio."""
    def __init__(self, codigo, tarifa):
        super().__init__(codigo)
        # La tarifa mínima es un centavo y el máximo se valida antes del registro.
        self._tarifa = numero(tarifa, "La tarifa", Decimal("0.01"), 100000000)

    # Cada especialidad establece su máximo de horas.
    @abstractmethod
    def validar(self, horas):
        """Devuelve la duración admitida por esta especialidad."""

    # El subtotal es propio de cada servicio, antes del descuento y del impuesto.
    @abstractmethod
    def subtotal(self, horas):
        """Calcula el costo antes de ajustes sobre una duración validada."""

    def calcular_costo(self, horas, *, descuento=0, impuesto=0):
        """Variantes por argumentos opcionales; primero descuento y luego impuesto."""
        # El método concreto se elige según el servicio que recibió la reserva.
        base = self.subtotal(self.validar(horas))
        # Ambos porcentajes admiten los extremos 0 y 100.
        rebaja = numero(descuento, "El descuento (%)", 0, 100)
        tasa = numero(impuesto, "El impuesto (%)", 0, 100)
        # Se aplica el impuesto al valor ya descontado y se redondea una sola vez.
        return (base * (1 - rebaja / 100) * (1 + tasa / 100)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP)


def horas_enteras(horas, limite):
    # La unidad mínima facturable es una hora.
    cantidad = numero(horas, "La duración en horas", 1, limite)
    # Comparar con el valor entero evita truncar solicitudes como 1,5 horas.
    if cantidad != cantidad.to_integral_value():
        raise DatoInvalido("La duración debe expresarse en horas enteras.")
    # A partir de aquí la duración puede usarse como número entero.
    return int(cantidad)


class Sala(Servicio):
    def validar(self, horas):
        # Una sala admite de una a ocho horas por reserva.
        return horas_enteras(horas, 8)

    def subtotal(self, horas):
        # La sala se factura por hora, sin cargo fijo.
        return self._tarifa * horas

    def describir(self):
        return f"{self.codigo} · sala por hora"


class Equipo(Servicio):
    def validar(self, horas):
        # El límite de alquiler de un equipo es un día.
        return horas_enteras(horas, 24)

    def subtotal(self, horas):
        # Cada alquiler incluye un cargo fijo de preparación.
        return self._tarifa * horas + 5000

    def describir(self):
        return f"{self.codigo} · equipo con preparación"


class Asesoria(Servicio):
    def validar(self, horas):
        # Una sesión de asesoría admite como máximo cuatro horas.
        return horas_enteras(horas, 4)

    def subtotal(self, horas):
        # La primera hora se cobra completa, las siguientes al 80 %.
        return self._tarifa * (1 + (horas - 1) * Decimal("0.80"))

    def describir(self):
        return f"{self.codigo} · asesoría especializada"


class Reserva(Entidad):
    def __init__(self, codigo, cliente, servicio, horas):
        super().__init__(codigo)
        # La reserva conserva las referencias al cliente y al servicio contratado.
        self.__cliente = cliente
        self.__servicio = servicio
        # El servicio valida su propia duración antes de aceptar la solicitud.
        self.__horas = servicio.validar(horas)
        # Una reserva nueva ocupa el recurso mientras espera confirmación.
        self.__estado = "pendiente"

    # Estas propiedades permiten consultar los vínculos y el estado sin reasignarlos.
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
        # Solo una solicitud pendiente admite la transición a confirmada.
        if self.estado != "pendiente":
            raise OperacionInvalida("Solo se confirma una reserva pendiente.")
        self.__estado = "confirmada"

    def cancelar(self):
        # Las reservas canceladas y procesadas ya están cerradas.
        if self.estado not in ("pendiente", "confirmada"):
            raise OperacionInvalida("La reserva ya está cerrada.")
        # El gestor volverá a considerar disponible este recurso.
        self.__estado = "cancelada"

    def procesar(self, **ajustes):
        # Exigir confirmación impide tanto el cobro anticipado como un segundo cobro.
        if self.estado != "confirmada":
            raise OperacionInvalida("Primero debe confirmar la reserva.")
        # Calcular antes de cerrar permite corregir un porcentaje y reintentar.
        total = self.servicio.calcular_costo(self.__horas, **ajustes)
        # La transición solo ocurre cuando el cálculo ha devuelto un importe válido.
        self.__estado = "procesada"
        return total

    def describir(self):
        # La descripción relaciona las tres claves con el estado para la bitácora.
        return f"{self.codigo} · {self.__cliente.codigo} · {self.servicio.codigo} · {self.estado}"

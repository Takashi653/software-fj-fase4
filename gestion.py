"""Colecciones en memoria y operaciones de la empresa."""
from modelo import (Asesoria, Cliente, DatoInvalido, Equipo, OperacionInvalida,
                    Reserva, Sala, texto)


class Gestion:
    tipos = {"sala": Sala, "equipo": Equipo, "asesoria": Asesoria}

    def __init__(self):
        self._clientes = []
        self._servicios = []
        self._reservas = []

    @staticmethod
    def _guardar(lista, objeto):
        """Comprueba la unicidad antes de añadir el objeto a la lista."""
        if any(item.codigo == objeto.codigo for item in lista):
            raise OperacionInvalida(f"El código {objeto.codigo} ya está registrado.")
        lista.append(objeto)
        return objeto.describir()

    @staticmethod
    def _buscar(lista, codigo):
        """Normaliza el código y localiza una entidad o informa de su ausencia."""
        clave = texto(codigo, "el código").upper()
        for objeto in lista:
            if objeto.codigo == clave:
                return objeto
        raise OperacionInvalida(f"No existe el código {clave}.")

    def cliente(self, codigo, nombre, correo):
        """Crea y valida el cliente antes de incorporarlo al registro."""
        return self._guardar(self._clientes, Cliente(codigo, nombre, correo))

    def servicio(self, tipo, codigo, tarifa):
        """Selecciona la clase especializada a partir del tipo solicitado."""
        try:
            clase = self.tipos[texto(tipo, "el tipo").lower()]
        except KeyError as causa:
            raise DatoInvalido("Tipo de servicio desconocido.") from causa
        return self._guardar(self._servicios, clase(codigo, tarifa))

    def reservar(self, codigo, cliente, servicio, horas=None):
        """Vincula cliente y servicio después de comprobar su disponibilidad."""
        if horas is None:
            raise DatoInvalido("Falta la duración de la reserva.")
        persona = self._buscar(self._clientes, cliente)
        recurso = self._buscar(self._servicios, servicio)
        # Un servicio representa una unidad, ocupada desde la solicitud hasta el cierre.
        if any(r.servicio is recurso and r.estado in ("pendiente", "confirmada")
               for r in self._reservas):
            raise OperacionInvalida(f"El servicio {recurso.codigo} está ocupado.")
        return self._guardar(self._reservas, Reserva(codigo, persona, recurso, horas))

    def confirmar(self, codigo):
        """Localiza la reserva y solicita la transición a confirmada."""
        reserva = self._buscar(self._reservas, codigo)
        reserva.confirmar()
        return reserva.describir()

    def cancelar(self, codigo):
        """Cierra la reserva para que el servicio pueda volver a solicitarse."""
        reserva = self._buscar(self._reservas, codigo)
        reserva.cancelar()
        return reserva.describir()

    def procesar(self, codigo, **ajustes):
        """Aplica los ajustes del cobro y devuelve el total en pesos."""
        reserva = self._buscar(self._reservas, codigo)
        total = reserva.procesar(**ajustes)
        return f"{reserva.describir()} · COP {total:.2f}"

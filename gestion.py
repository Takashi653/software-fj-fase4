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
        if any(item.codigo == objeto.codigo for item in lista):
            raise OperacionInvalida(f"El código {objeto.codigo} ya está registrado.")
        lista.append(objeto)
        return objeto.describir()

    @staticmethod
    def _buscar(lista, codigo):
        clave = texto(codigo, "el código").upper()
        for objeto in lista:
            if objeto.codigo == clave:
                return objeto
        raise OperacionInvalida(f"No existe el código {clave}.")

    def cliente(self, codigo, nombre, correo):
        return self._guardar(self._clientes, Cliente(codigo, nombre, correo))

    def servicio(self, tipo, codigo, tarifa):
        try:
            clase = self.tipos[texto(tipo, "el tipo").lower()]
        except KeyError as causa:
            raise DatoInvalido("Tipo de servicio desconocido.") from causa
        return self._guardar(self._servicios, clase(codigo, tarifa))

    def reservar(self, codigo, cliente, servicio, horas=None):
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
        reserva = self._buscar(self._reservas, codigo)
        reserva.confirmar()
        return reserva.describir()

    def cancelar(self, codigo):
        reserva = self._buscar(self._reservas, codigo)
        reserva.cancelar()
        return reserva.describir()

    def procesar(self, codigo, **ajustes):
        reserva = self._buscar(self._reservas, codigo)
        total = reserva.procesar(**ajustes)
        return f"{reserva.describir()} · COP {total:.2f}"
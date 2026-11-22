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

    def cliente(self, codigo, nombre, correo, *, editar=False):
        """Crea y valida el cliente antes de incorporarlo al registro."""
        return self._registrar(self._clientes, Cliente(codigo, nombre, correo), editar)

    def servicio(self, tipo, codigo, tarifa, *, editar=False):
        """Selecciona la clase especializada a partir del tipo solicitado."""
        try:
            clase = self.tipos[texto(tipo, "el tipo").lower()]
        except KeyError as causa:
            raise DatoInvalido("Tipo de servicio desconocido.") from causa
        return self._registrar(self._servicios, clase(codigo, tarifa), editar)

    def reservar(self, codigo, cliente, servicio, horas=None, *, editar=False):
        """Vincula cliente y servicio después de comprobar su disponibilidad."""
        if horas is None:
            raise DatoInvalido("Falta la duración de la reserva.")
        persona = self._buscar(self._clientes, cliente)
        recurso = self._buscar(self._servicios, servicio)
        anterior = self._buscar(self._reservas, codigo) if editar else None
        if anterior is not None:
            if anterior.estado not in ("pendiente", "confirmada"):
                raise OperacionInvalida("La reserva ya está cerrada.")
            if anterior.servicio.codigo == recurso.codigo:
                # El recurso original conserva la tarifa acordada al reservar.
                recurso = anterior.servicio
        if any(r is not anterior and r.servicio.codigo == recurso.codigo
               and r.estado in ("pendiente", "confirmada") for r in self._reservas):
            raise OperacionInvalida(f"El servicio {recurso.codigo} está ocupado.")
        nueva = Reserva(codigo, persona, recurso, horas)
        if anterior is not None and anterior.estado == "confirmada":
            nueva.confirmar()
        return self._registrar(self._reservas, nueva, editar)

    def _registrar(self, lista, objeto, editar):
        if not editar:
            return self._guardar(lista, objeto)
        previo = self._buscar(lista, objeto.codigo)
        lista[lista.index(previo)] = objeto
        return objeto.describir()

    def borrar(self, tipo, codigo):
        listas = {"cliente": self._clientes, "servicio": self._servicios, "reserva": self._reservas}
        lista = listas[tipo]
        objeto = self._buscar(lista, codigo)
        if tipo in ("cliente", "servicio"):
            vinculadas = [r.codigo for r in self._reservas if getattr(r, tipo).codigo == objeto.codigo]
            if vinculadas:
                raise OperacionInvalida("Tiene reservas asociadas: " + ", ".join(vinculadas))
        lista.remove(objeto)
        return f"Registro eliminado: {objeto.codigo}."

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

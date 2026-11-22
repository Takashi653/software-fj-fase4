"""Panel local de Software FJ. Iniciar con python interfaz.py."""
import io
import json
import logging
import secrets
import sys
import webbrowser
from contextlib import redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock, Thread

from gestion import Gestion
from modelo import DatoInvalido, ErrorGestion
from principal import ejecutar

BASE = Path(__file__).resolve().parent


class Panel:
    """Mantiene las filas visibles de la sesión junto al gestor de dominio."""
    def __init__(self):
        self.gestion = Gestion()
        self.clientes, self.servicios, self.reservas = [], [], []
        self.pruebas = []
        # Datos iniciales ficticios para poder probar una reserva de inmediato.
        for codigo, nombre in [("C1", "Ana Ríos"), ("C2", "Luis Mora")]:
            self.operar("cliente", dict(codigo=codigo, nombre=nombre, correo=codigo+"@example.org"))
        for tipo, codigo, tarifa in [("sala", "S1", 30000), ("equipo", "E1", 10000), ("asesoria", "A1", 50000)]:
            self.operar("servicio", dict(tipo=tipo, codigo=codigo, tarifa=tarifa))

    def datos(self):
        return dict(clientes=self.clientes, servicios=self.servicios, reservas=self.reservas, pruebas=self.pruebas)

    def operar(self, accion, datos):
        g = self.gestion
        codigo = str(datos.get("codigo", "")).strip().upper()
        if accion == "cliente":
            nombre, correo = datos["nombre"].strip(), datos["correo"].strip()
            resultado = g.cliente(codigo, nombre, correo)
            self.clientes.append(dict(codigo=codigo, nombre=nombre, correo=correo))
        elif accion == "servicio":
            tipo, tarifa = datos["tipo"], datos["tarifa"]
            resultado = g.servicio(tipo, codigo, tarifa)
            self.servicios.append(dict(codigo=codigo, tipo=tipo, tarifa=float(tarifa)))
        elif accion == "reservar":
            cliente, recurso, horas = datos["cliente"], datos["servicio"], datos["horas"]
            resultado = g.reservar(codigo, cliente, recurso, horas)
            self.reservas.insert(0, dict(codigo=codigo, cliente=cliente, servicio=recurso, horas=int(float(horas)), estado="pendiente", total=None))
        elif accion in ("confirmar", "cancelar", "procesar"):
            reserva = next((r for r in self.reservas if r["codigo"] == codigo), None)
            if reserva is None:
                raise DatoInvalido("La reserva no existe.")
            if accion == "procesar":
                resultado = g.procesar(codigo, descuento=datos.get("descuento", 0), impuesto=datos.get("impuesto", 0))
                reserva["total"] = float(resultado.rsplit(" COP ", 1)[1])
                reserva["estado"] = "procesada"
            elif accion == "confirmar":
                resultado = g.confirmar(codigo)
                reserva["estado"] = "confirmada"
            else:
                resultado = g.cancelar(codigo)
                reserva["estado"] = "cancelada"
        elif accion == "simular":
            salida = io.StringIO()
            with redirect_stdout(salida):
                ejecutar()
            self.pruebas = []
            for linea in salida.getvalue().splitlines()[:-1]:
                caso, estado, detalle = linea.split(" | ", 2)
                self.pruebas.append(dict(caso=caso, estado=estado, detalle=detalle))
            resultado = salida.getvalue().splitlines()[-1]
        else:
            raise DatoInvalido("Operación desconocida.")
        logging.getLogger("panel_fj").info("%s | %s", accion, resultado)
        return resultado


class Solicitud(BaseHTTPRequestHandler):
    """Atiende únicamente a la aplicación del mismo origen en el equipo local."""
    def log_message(self, fmt, *args):
        pass

    def responder(self, codigo, contenido, tipo):
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(contenido)))
        self.end_headers()
        self.wfile.write(contenido)

    def json(self, codigo, valor):
        self.responder(codigo, json.dumps(valor, ensure_ascii=False).encode(), "application/json; charset=utf-8")

    def do_GET(self):
        if self.headers.get("Host") != self.server.host:
            return self.send_error(403)
        if self.path == "/":
            html = (BASE / "panel.html").read_text(encoding="utf-8-sig")
            self.responder(200, html.replace("TOKEN_LOCAL", self.server.token).encode(), "text/html; charset=utf-8")
        elif self.path == "/estado":
            with self.server.lock:
                self.json(200, self.server.panel.datos())
        else:
            self.send_error(404)

    def do_POST(self):
        if (self.headers.get("Host") != self.server.host or
                self.headers.get("X-FJ") != self.server.token or self.path != "/operar"):
            return self.send_error(403)
        try:
            largo = int(self.headers.get("Content-Length", 0))
            if not 0 < largo <= 16384:
                raise DatoInvalido("Solicitud fuera de los límites.")
            peticion = json.loads(self.rfile.read(largo))
            if peticion["accion"] == "salir":
                self.json(200, dict(cerrado=True))
                Thread(target=self.server.shutdown, daemon=True).start()
                return
            with self.server.lock:
                mensaje = self.server.panel.operar(peticion["accion"], peticion["datos"])
                respuesta = json.loads(json.dumps(self.server.panel.datos()))
        except (ErrorGestion, ValueError, TypeError, KeyError, AttributeError) as causa:
            logging.getLogger("panel_fj").exception("Operación rechazada")
            self.json(400, dict(error=str(causa)))
        except Exception:
            logging.getLogger("panel_fj").exception("Error imprevisto en el panel")
            self.json(500, dict(error="No se pudo completar la operación. Consulte la bitácora."))
        else:
            self.json(200, dict(mensaje=mensaje, estado=respuesta))


def iniciar():
    registro = logging.getLogger("panel_fj")
    registro.setLevel(logging.INFO)
    archivo = logging.FileHandler(BASE / "software_fj.log", encoding="utf-8")
    archivo.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    registro.addHandler(archivo)
    puerto = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    with ThreadingHTTPServer(("127.0.0.1", puerto), Solicitud) as servidor:
        servidor.host = "127.0.0.1:" + str(servidor.server_port)
        servidor.token = secrets.token_urlsafe(32)
        servidor.lock = Lock()
        servidor.panel = Panel()
        url = "http://" + servidor.host + "/"
        if "--sin-abrir" not in sys.argv:
            webbrowser.open(url)
        try:
            servidor.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    iniciar()

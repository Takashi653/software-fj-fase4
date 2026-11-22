"""Ejecute este archivo para reproducir los casos del componente práctico."""
import logging
from pathlib import Path

from gestion import Gestion
from modelo import ErrorGestion


def simulaciones(g):
    """Cada fila indica el caso, la función y los argumentos que se probarán."""
    return [
        ("Alta de cliente", g.cliente, ("C1", "Ana Ríos", "ana@example.org"), {}),
        ("Correo incompleto", g.cliente, ("C2", "Luis Mora", "luis@"), {}),
        ("Correo corregido", g.cliente, ("C2", "Luis Mora", "luis@example.org"), {}),
        ("Código duplicado", g.cliente, ("c1", "Ana Ríos", "ana@example.org"), {}),
        ("Registrar sala", g.servicio, ("sala", "S1", 30000), {}),
        ("Tarifa no numérica", g.servicio, ("equipo", "E1", "diez"), {}),
        ("Registrar equipo", g.servicio, ("equipo", "E1", 10000), {}),
        ("Registrar asesoría", g.servicio, ("asesoria", "A1", 50000), {}),
        ("Tipo desconocido", g.servicio, ("viaje", "V1", 10000), {}),
        ("Cliente desconocido", g.reservar, ("R0", "C9", "S1", 1), {}),
        ("Exceso de horas", g.reservar, ("R0", "C1", "A1", 5), {}),
        ("Reservar sala", g.reservar, ("R1", "C1", "S1", 2), {}),
        ("Servicio ocupado", g.reservar, ("R2", "C2", "S1", 2), {}),
        ("Procesar sin confirmar", g.procesar, ("R1",), {}),
        ("Confirmar sala", g.confirmar, ("R1",), {}),
        ("Descuento excesivo", g.procesar, ("R1",), {"descuento": 110}),
        ("Cobrar sala con ajustes", g.procesar, ("R1",), {"descuento": 10, "impuesto": 19}),
        ("Reutilizar sala liberada", g.reservar, ("R2", "C2", "S1", 1), {}),
        ("Cancelar sala", g.cancelar, ("R2",), {}),
        ("Repetir cancelación", g.cancelar, ("R2",), {}),
        ("Reservar equipo", g.reservar, ("R3", "C2", "E1", 3), {}),
        ("Confirmar equipo", g.confirmar, ("R3",), {}),
        ("Cobrar equipo", g.procesar, ("R3",), {}),
        ("Falta la duración", g.reservar, ("R4", "C1", "A1"), {}),
        ("Reservar asesoría", g.reservar, ("R4", "C1", "A1", 2), {}),
        ("Confirmar asesoría", g.confirmar, ("R4",), {}),
        ("Cobrar asesoría", g.procesar, ("R4",), {}),
    ]


def ejecutar():
    registro = logging.getLogger("software_fj")
    registro.setLevel(logging.INFO)
    ruta = Path(__file__).resolve().with_name("software_fj.log")
    try:
        archivo = logging.FileHandler(ruta, encoding="utf-8")
    except OSError as causa:
        print(f"Registro en consola: no se pudo abrir el archivo ({causa}).")
        archivo = logging.StreamHandler()
    archivo.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    registro.addHandler(archivo)
    exitos = rechazos = imprevistos = 0
    try:
        registro.info("INICIO DE SIMULACIÓN")
        for n, (caso, accion, args, opciones) in enumerate(simulaciones(Gestion()), 1):
            etiqueta = f"{n:02d} {caso}"
            try:
                detalle = accion(*args, **opciones)
            except ErrorGestion as causa:
                # Conserva el traceback y cualquier excepción encadenada en el log.
                rechazos += 1
                registro.exception("%s | RECHAZADA", etiqueta)
                mensaje = f"RECHAZADA | {causa}"
            except Exception as causa:
                # Última barrera por operación: distingue fallos de programación.
                imprevistos += 1
                registro.exception("%s | IMPREVISTA", etiqueta)
                mensaje = f"IMPREVISTA | {causa}"
            else:
                exitos += 1
                registro.info("%s | ACEPTADA | %s", etiqueta, detalle)
                mensaje = f"ACEPTADA | {detalle}"
            finally:
                registro.info("%s | FIN DE OPERACIÓN", etiqueta)
            print(f"{etiqueta} | {mensaje}")
        resumen = f"{exitos} aceptadas, {rechazos} rechazadas, {imprevistos} imprevistas."
        registro.info("RESUMEN | %s", resumen)
        print(resumen)
    finally:
        registro.removeHandler(archivo)
        archivo.close()
    return imprevistos


if __name__ == "__main__":
    raise SystemExit(bool(ejecutar()))
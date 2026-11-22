"""Punto de entrada de Software FJ para ejecutar las 27 simulaciones."""
from principal import ejecutar  # Reutiliza el mismo flujo documentado en el foro.


if __name__ == "__main__":
    # Cero indica que todas las operaciones terminaron sin errores imprevistos.
    raise SystemExit(bool(ejecutar()))

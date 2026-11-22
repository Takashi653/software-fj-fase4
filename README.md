# Software FJ

**Presentación individual:** Atanael Balaguera Barbosa · Grupo 61.

Ejecute `python main.py` desde la raíz del proyecto. Este punto de entrada reproduce las 27 operaciones de `principal.py`.
Sistema de clientes, servicios y reservas para la práctica simulada de Programación (213023). Los ejemplos utilizan datos ficticios.

## Ejecutar la simulación
Desde esta carpeta, con Python 3.8 o posterior, ejecute:

    python principal.py

En Windows también puede usar `py principal.py`. Las 27 operaciones se ejecutan en orden y presentan el resultado en consola. El resumen esperado es **16 aceptadas, 11 rechazadas y 0 imprevistas**. Cada ejecución inicia con listas vacías y agrega una sesión a `software_fj.log`. Se requiere permiso de escritura en la carpeta para conservar la bitácora.

## Organización
- `modelo.py` define clientes, servicios, reservas, excepciones y validadores.
- `gestion.py` registra y busca entidades en listas, valida disponibilidad y coordina cambios de estado.
- `principal.py` ejecuta los casos e identifica cada resultado en consola y en el log.
- `software_fj.log` contiene una ejecución de referencia. Busque el número del caso y el marcador FIN DE OPERACIÓN para seguirlo.

## Reglas de la simulación
Cada código de servicio identifica una unidad. Una reserva pendiente o confirmada ocupa la unidad hasta su cancelación o procesamiento. Las duraciones son enteras. La sala admite de 1 a 8 horas y se cobra por hora. El equipo admite de 1 a 24 horas y suma 5.000 COP por preparación. La asesoría admite de 1 a 4 horas y aplica el 80 % de la tarifa desde la segunda hora. Los ajustes opcionales se expresan de 0 a 100, primero se descuenta y después se aplica el impuesto. Los valores son supuestos del ejercicio.

## Resultados para contrastar
- Casos 12 a 19. La segunda solicitud sobre la sala ocupada falla. El descuento excesivo preserva la reserva confirmada y el reintento cobra 64.260 COP. La sala vuelve a estar disponible.
- Casos 20 a 23. La segunda cancelación falla. El alquiler de tres horas termina con un cobro de 35.000 COP.
- Casos 24 a 27. La solicitud sin duración falla. La asesoría de dos horas termina con un cobro de 90.000 COP.

Los errores de dominio conservan un mensaje legible. Cuando una conversión falla, el log conserva también la excepción original. Un fallo imprevisto se cuenta por separado y produce un código de salida distinto de cero al terminar la serie.

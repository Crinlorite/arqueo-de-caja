# Arqueo de Caja

Aplicacion de escritorio para realizar arqueos de caja de forma rapida y sencilla. Hecha con Python y tkinter, empaquetada como `.exe` portable (no requiere instalacion ni permisos de administrador). Formato de ticket compacto optimizado para impresoras de tickets.

## Funcionalidades

- **Tabla de billetes y monedas** con todas las denominaciones del euro (500€ a 0.01€)
- **Calculo en tiempo real** al introducir unidades
- **Campo Trabajador** para identificar quien realiza el arqueo
- **Fondo fijo de caja** editable (por defecto 350€), con resultado automatico (Total - Fondo fijo)
- **Memoria persistente**: al cerrar la app se guardan las unidades, el fondo fijo y el trabajador, y se restauran al volver a abrir
- **Exportar resumen**: genera un archivo `.txt` con formato ticket compacto en la carpeta `arqueos/`
- **Auto-exportacion al cerrar**: nunca se pierde un arqueo aunque se olvide exportar manualmente
- **Impresion directa**: envía el ticket en modo RAW ESC/POS — sin márgenes, sin cambiar la impresora predeterminada del sistema
- **Configuracion de impresora**: selección guardada en la app, no afecta al resto del sistema
- **Cargar sesion anterior**: lista los arqueos guardados con fecha, hora y trabajador, con buscador que filtra por palabras (dia, año, nombre...)
- **Limpiar campos**: resetea todas las unidades de golpe

## Impresora de tickets

Impresión directa vía `win32print` (RAW ESC/POS). Compatible con Epson TM-T20 y similares.

- Sin Notepad, sin PowerShell, sin márgenes GDI
- Encoding **CP858** (español + `€`)
- Texto centrado automáticamente
- Corte automático `GS V 0` con 4 líneas de avance

**Requisito**: `pywin32`

```bash
pip install pywin32
```

## Uso

Ejecuta `Arqueo de Caja.exe` directamente. No necesita Python instalado.

Los archivos generados se guardan junto al `.exe`:
- `arqueo_config.json` — configuracion, estado persistente e impresora seleccionada
- `arqueos/` — carpeta con los resumenes exportados (tickets `.txt`)

## Compilar desde el codigo fuente

```bash
pip install pyinstaller pywin32
pyinstaller --onefile --noconsole --name "Arqueo de Caja" arqueo.py
```

El ejecutable se genera en la carpeta `dist/`.

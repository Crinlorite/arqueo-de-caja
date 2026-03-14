# Arqueo de Caja

Aplicacion de escritorio para realizar arqueos de caja de forma rapida y sencilla. Hecha con Python y tkinter, empaquetada como `.exe` portable (no requiere instalacion ni permisos de administrador).

## Funcionalidades

- **Tabla de billetes y monedas** con todas las denominaciones del euro (500€ a 0.01€)
- **Calculo en tiempo real** al introducir unidades
- **Fondo fijo de caja** editable (por defecto 350€), con resultado automatico (Total - Fondo fijo)
- **Memoria persistente**: al cerrar la app se guardan las unidades y el fondo fijo, y se restauran al volver a abrir
- **Exportar resumen**: genera un archivo `.txt` con fecha, hora y desglose completo en la carpeta `arqueos/`
- **Limpiar campos**: resetea todas las unidades de golpe

## Uso

Ejecuta `Arqueo de Caja.exe` directamente. No necesita Python instalado.

Los archivos generados se guardan junto al `.exe`:
- `arqueo_config.json` — configuracion y estado persistente
- `arqueos/` — carpeta con los resumenes exportados

## Compilar desde el codigo fuente

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole --name "Arqueo de Caja" arqueo.py
```

El ejecutable se genera en la carpeta `dist/`.

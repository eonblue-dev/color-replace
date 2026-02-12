# Color Replace App

Aplicacion de escritorio para reemplazar un color objetivo por un color destino en una imagen usando OpenCV.
Incluye una interfaz grafica con controles de tolerancia y mezcla, y permite seleccionar el color objetivo con un click.

## Estructura del proyecto

- app.py: Interfaz grafica (Tkinter). Maneja la carga de imagen, eventos y la visualizacion.
- logic.py: Logica de procesamiento de imagen (mascara HSV, reemplazo de color, preview).

## Presentacion

- Ver [PRESENTACION_MARP.md](PRESENTACION_MARP.md) (formato Marp, lista para exponer)

## Requisitos

- Python 3.9+ (recomendado)
- Dependencias:
  - opencv-python
  - numpy
  - pillow

Instalacion rapida:

```bash
pip install opencv-python numpy pillow
```

## Ejecucion

Desde la carpeta del proyecto:

```bash
python app.py
```

Si `python` no funciona en Windows, puedes usar:

```bash
py app.py
```

## Uso basico

1. Clic en "Cargar imagen" y selecciona un archivo JPG/PNG/BMP.
2. Define el color objetivo (el que quieres cambiar):
  - Opcion A: Clic en "Seleccionar con click" y luego clic sobre el color objetivo en la imagen.
  - Opcion B: Clic en "Elegir color objetivo..." y selecciona el color desde el picker.
3. Clic en "Elegir color destino..." para definir el nuevo color.
4. Ajusta los controles si es necesario:
   - Tolerancia (HSV): que tan amplio es el rango del color objetivo.
   - Suavizado (feather): suaviza bordes de la mascara.
   - Morph iteraciones: limpia ruido con morfologia.
   - Fuerza de mezcla: intensidad del reemplazo.
   - Mantener brillo (V): conserva el brillo original.
5. Clic en "Procesar" para aplicar el reemplazo.

## Notas de funcionamiento

- El color objetivo se trabaja en HSV para una seleccion mas robusta.
- La mascara se suaviza con blur y se limpia con operaciones morfologicas.
- El reemplazo mezcla el color destino con un alpha basado en la mascara.

## Solucion de problemas

- Si ves errores de dependencias, instala los paquetes con el comando de arriba.
- Si la imagen no se carga, verifica que el archivo sea JPG/PNG/BMP valido.

## Licencia

Este proyecto no incluye una licencia explicita. Agrega una si lo vas a distribuir.

# Color Replace (OpenCV + Tkinter)

App de escritorio en Python para **reemplazar (o recolorear)** un color específico dentro de una imagen usando **selección por similitud en HSV**.

- Selecciona el color a cambiar con **un click** sobre la imagen (o con un **color picker**).
- Elige el color nuevo (destino).
- Ajusta tolerancia y suavizado para afinar la máscara.
- Aplica el reemplazo con una **fuerza de mezcla** configurable y opción de **mantener brillo**.

---

## Qué resuelve

Cuando quieres recolorear una zona (ropa, objetos, logos, paredes, etc.), hacerlo a mano puede ser lento. Este proyecto automatiza el proceso mediante una máscara en HSV y te da controles simples para afinar el resultado.

---

## Funcionalidades

- Carga de imágenes (`.jpg`, `.png`, `.bmp`, …).
- Selección del color objetivo:
  - Click sobre la imagen (modo “pick”).
  - Selector de color (alternativa rápida).
- Selección del color destino con selector de color.
- Vista previa de selección (tinte rojo) para validar la máscara.
- Reemplazo con mezcla controlada:
  - **Tolerancia (HSV)**
  - **Suavizado (feather)**
  - **Limpieza morfológica (morph)**
  - **Fuerza de mezcla**
  - **Mantener brillo (canal V)**

---

## Tecnologías

- Python 3
- Tkinter (UI)
- OpenCV (procesamiento de imagen)
- NumPy (operaciones vectorizadas)
- Pillow (render en Tkinter)

---

## Instalación

### Requisitos

- Python 3.9+ (recomendado)
- Windows / macOS / Linux

### Dependencias

Instala dependencias con pip:

```bash
pip install opencv-python numpy pillow
```

> Tkinter suele venir con Python en Windows. En Linux puede requerir instalación adicional (por ejemplo `python3-tk`).

---

## Ejecución

Desde la carpeta del proyecto:

```bash
python app.py
```

---

## Cómo usar

1. **Cargar imagen**.
2. Elegir el **color a cambiar (objetivo)**:
   - Botón “Elegir color a cambiar (click)” y luego click en la imagen, o
   - Botón “Elegir color a cambiar (picker)…”.
3. Elegir el **color nuevo (destino)**.
4. Ajustar sliders:
   - **Tolerancia (HSV)**: qué tan “cerca” del color objetivo se selecciona.
   - **Suavizado (feather)**: suaviza bordes de la máscara.
   - **Morph iteraciones**: elimina ruido (open/close).
   - **Fuerza de mezcla**: intensidad del cambio.
   - **Mantener brillo (V)**: conserva iluminación/sombras originales.
5. Pulsar **Procesar**.

---

## Notas técnicas (resumen)

- El proyecto trabaja en HSV con el formato de OpenCV:
  - H: 0..179, S: 0..255, V: 0..255.
- La máscara se construye con `cv2.inRange` y maneja el **wrap-around** del tono (H) cerca de 0/179.
- La “fuerza de mezcla” es un **blending parcial por píxel** usando una alpha derivada de la máscara:
  - \(\alpha = (mask/255) \cdot (fuerza/100)\)
  - Mezcla H/S hacia el destino, y V se mantiene o también se mezcla según la opción.

---

## Estructura del proyecto

- `app.py`: interfaz (Tkinter), eventos, canvas, carga y visualización.
- `logic.py`: procesamiento (máscara HSV, reemplazo de color, vista previa).

---

## Limitaciones

- La selección es por **similitud de color**, no por “objeto”: si el color aparece en varias zonas, se afectarán todas.
- Sensible a iluminación, sombras, reflejos y compresión (por ejemplo JPEG): puede incluir/excluir píxeles inesperados.
- No maneja canal alfa (transparencia) de forma explícita.

---

## Próximos pasos (ideas)

- Ajustes de tolerancia separados para H / S / V.
- Exportar resultado a archivo desde la UI.
- Soporte para PNG con alpha (cuando aplique).

---

## Autor / Contacto

- Nombre: *Pedro Luis*
- LinkedIn: *www.linkedin.com/in/pedrl-rf01*

---

## Licencia

“Proyecto educativo/portfolio”.

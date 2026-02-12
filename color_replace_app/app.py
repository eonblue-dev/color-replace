import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox

import logic

try:
    import cv2
    import numpy as np
except Exception:
    cv2 = None
    np = None

try:
    from PIL import Image, ImageTk
except Exception:
    Image = None
    ImageTk = None

logic.cv2 = cv2
logic.np = np


# App de escritorio (Tkinter) para reemplazar un color en una imagen usando OpenCV.
#
# Idea general del proyecto:
# - `app.py` = capa de UI: botones, sliders, canvas, eventos, mostrar imágenes.
# - `logic.py` = capa de procesamiento: máscara HSV, reemplazo de color, preview.
#
# Nota sobre dependencias:
# - Importamos `cv2`/`numpy`/`PIL` con try/except para dar errores amigables.
# - Luego asignamos `logic.cv2 = cv2` y `logic.np = np` para que `logic.py` use
#   las mismas dependencias (o detecte si faltan).
class ColorReplaceApp:

    # Constructor: recibe el root de Tkinter y prepara el estado inicial.
    # Aquí se definen variables que se irán actualizando durante el uso.
    def __init__(self, root):
        self.root = root
        self.root.title("Color Replace - OpenCV")
        self.root.geometry("1200x700")

        self.image_bgr = None
        self.image_hsv = None
        self.result_bgr = None
        self.pick_mode = False
        self.picked_hsv = None
        self.target_hsv = (30, 200, 200)
        self.display_info = None

        self._build_ui()

    # Construye toda la interfaz:
    # - Panel izquierdo: botones y controles (sliders/checkbox)
    # - Panel derecho: canvas donde se dibuja la imagen
    # También conecta el click del canvas al método `on_canvas_click`.
    def _build_ui(self):
        self.left = tk.Frame(self.root, padx=10, pady=10)
        self.left.pack(side=tk.LEFT, fill=tk.Y)

        self.right = tk.Frame(self.root, padx=10, pady=10)
        self.right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        tk.Label(self.left, text="Carga y opciones", font=("Arial", 12, "bold")).pack(anchor="w")

        tk.Button(self.left, text="Cargar imagen", command=self.load_image).pack(fill=tk.X, pady=5)
        tk.Button(self.left, text="Ver original", command=self.show_original).pack(fill=tk.X, pady=5)

        tk.Label(self.left, text="Color a cambiar (objetivo)").pack(anchor="w", pady=(10, 0))
        tk.Button(self.left, text="Elegir color a cambiar (click)", command=self.enable_pick).pack(fill=tk.X, pady=5)
        tk.Button(self.left, text="Elegir color a cambiar (picker)...", command=self.choose_source_color).pack(fill=tk.X, pady=5)

        tk.Label(self.left, text="Color nuevo (destino)").pack(anchor="w", pady=(10, 0))
        tk.Button(self.left, text="Elegir color nuevo (destino)...", command=self.choose_target_color).pack(fill=tk.X, pady=5)

        tk.Label(self.left, text="Tolerancia (HSV)").pack(anchor="w", pady=(10, 0))
        self.tol_var = tk.IntVar(value=20)
        tk.Scale(self.left, from_=0, to=60, orient=tk.HORIZONTAL, variable=self.tol_var).pack(fill=tk.X)

        tk.Label(self.left, text="Suavizado (feather)").pack(anchor="w", pady=(10, 0))
        self.blur_var = tk.IntVar(value=7)
        tk.Scale(self.left, from_=1, to=31, orient=tk.HORIZONTAL, variable=self.blur_var).pack(fill=tk.X)

        tk.Label(self.left, text="Morph iteraciones").pack(anchor="w", pady=(10, 0))
        self.morph_var = tk.IntVar(value=1)
        tk.Scale(self.left, from_=0, to=8, orient=tk.HORIZONTAL, variable=self.morph_var).pack(fill=tk.X)

        tk.Label(self.left, text="Fuerza de mezcla").pack(anchor="w", pady=(10, 0))
        self.mix_var = tk.IntVar(value=80)
        tk.Scale(self.left, from_=0, to=100, orient=tk.HORIZONTAL, variable=self.mix_var).pack(fill=tk.X)

        self.keep_v_var = tk.BooleanVar(value=True)
        tk.Checkbutton(self.left, text="Mantener brillo (V)", variable=self.keep_v_var).pack(anchor="w", pady=(8, 0))

        tk.Button(self.left, text="Procesar", command=self.process).pack(fill=tk.X, pady=10)

        self.status = tk.Label(self.left, text="Listo", fg="gray")
        self.status.pack(anchor="w", pady=(10, 0))

        self.canvas = tk.Canvas(self.right, bg="#222")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self.on_canvas_click)

    # Abre un diálogo para elegir una imagen y la carga con OpenCV.
    # Guarda:
    # - `image_bgr`: imagen original (BGR, OpenCV)
    # - `image_hsv`: la misma imagen convertida a HSV (para seleccionar/reemplazar)
    # Y muestra la imagen en el canvas.
    def load_image(self):
        if cv2 is None or Image is None:
            messagebox.showerror("Error", "Faltan dependencias: cv2 o PIL.")
            return

        path = filedialog.askopenfilename(
            filetypes=[("Imagen", "*.jpg *.jpeg *.png *.bmp")]
        )
        if not path:
            return

        self.image_bgr = cv2.imread(path)
        if self.image_bgr is None:
            messagebox.showerror("Error", "No se pudo cargar la imagen.")
            return

        self.image_hsv = cv2.cvtColor(self.image_bgr, cv2.COLOR_BGR2HSV)
        self.result_bgr = None
        self.picked_hsv = None

        self.show_image(self.image_bgr)
        self.status.config(text="Imagen cargada")

    # Vuelve a mostrar la imagen original (si hay una cargada).
    # Útil para comparar con el resultado procesado.
    def show_original(self):
        if self.image_bgr is None:
            return
        self.show_image(self.image_bgr)
        self.status.config(text="Mostrando original")

    # Activa el “modo selección”: el próximo click en el canvas capturará el color objetivo.
    def enable_pick(self):
        self.pick_mode = True
        self.status.config(text="Selecciona en la imagen el color A CAMBIAR")

    # Abre el selector de color (Tkinter) para elegir el color destino.
    # El selector devuelve RGB, y lo convertimos a HSV de OpenCV usando `logic.convertir_rgb_a_hsv`.
    def choose_target_color(self):
        color = colorchooser.askcolor(title="Selecciona color NUEVO (destino)")
        if not color or color[0] is None:
            return
        r, g, b = [int(c) for c in color[0]]
        self.target_hsv = logic.convertir_rgb_a_hsv(r, g, b)
        if self.picked_hsv is None:
            self.status.config(text=f"Destino HSV: {self.target_hsv} (ahora elige el color a cambiar)")
        else:
            self.status.config(text=f"Objetivo HSV: {self.picked_hsv} | Destino HSV: {self.target_hsv}")

    # Permite elegir el color objetivo (el que quieres cambiar) usando el selector de color.
    # Esto es una alternativa a seleccionar con click en la imagen.
    #
    # Flujo:
    # - Pide un color RGB al usuario.
    # - Lo convierte a HSV (formato OpenCV) con `logic.convertir_rgb_a_hsv`.
    # - Lo guarda en `picked_hsv` para que `process()` pueda usarlo.
    # - Si hay imagen cargada, muestra la preview de selección.
    def choose_source_color(self):
        color = colorchooser.askcolor(title="Selecciona color A CAMBIAR (objetivo)")
        if not color or color[0] is None:
            return

        r, g, b = [int(c) for c in color[0]]
        self.picked_hsv = logic.convertir_rgb_a_hsv(r, g, b)
        self.pick_mode = False

        if self.image_hsv is None:
            self.status.config(text=f"Objetivo HSV: {self.picked_hsv} (carga una imagen para ver preview)")
            return

        self._show_selection_preview()
        self.status.config(text=f"Objetivo HSV: {self.picked_hsv} | Destino HSV: {self.target_hsv}")

    # Maneja el click en el canvas.
    # Si `pick_mode` está activo:
    # - Convierte la coordenada del click (canvas) a coordenadas reales de la imagen.
    # - Lee el pixel HSV en esa posición y lo guarda como `picked_hsv`.
    # - Muestra una vista previa de selección (tinte rojo) para verificar la máscara.
    #
    # Importante: la imagen se dibuja escalada en el canvas. Por eso usamos `display_info`
    # (guardado en `_show_on_canvas`) para mapear correctamente el click.
    def on_canvas_click(self, event):
        if not self.pick_mode or self.image_hsv is None or self.display_info is None:
            return

        x, y = event.x, event.y
        x0, y0 = self.display_info["x0"], self.display_info["y0"]
        dw, dh = self.display_info["dw"], self.display_info["dh"]
        scale = self.display_info["scale"]

        if x < x0 or y < y0 or x >= x0 + dw or y >= y0 + dh:
            return

        ix = int((x - x0) / scale)
        iy = int((y - y0) / scale)

        h, w = self.image_hsv.shape[:2]
        if ix < 0 or iy < 0 or ix >= w or iy >= h:
            return

        hsv = self.image_hsv[iy, ix]
        self.picked_hsv = (int(hsv[0]), int(hsv[1]), int(hsv[2]))
        self.pick_mode = False
        self._show_selection_preview()
        self.status.config(text=f"Objetivo HSV: {self.picked_hsv} | Destino HSV: {self.target_hsv}")

    # Botón principal de procesamiento.
    # Flujo:
    # 1) Valida dependencias y que exista imagen + color objetivo.
    # 2) Crea máscara HSV llamando a `logic.crear_mascara_hsv`.
    # 3) Reemplaza el color llamando a `logic.reemplazar_color`.
    # 4) Muestra el resultado en el canvas.
    def process(self):
        if cv2 is None or np is None:
            messagebox.showerror("Error", "Faltan dependencias: cv2 o numpy.")
            return
        if self.image_hsv is None:
            messagebox.showwarning("Aviso", "Carga una imagen primero.")
            return
        if self.picked_hsv is None:
            messagebox.showwarning(
                "Aviso",
                "Primero elige el color A CAMBIAR (objetivo) con click o con el picker.",
            )
            return

        mask = logic.crear_mascara_hsv(
            self.image_hsv,
            self.picked_hsv,
            self.tol_var.get(),
            self.blur_var.get(),
            self.morph_var.get(),
        )
        if mask is None:
            messagebox.showerror("Error", "No se pudo crear la mascara.")
            return

        self.result_bgr = logic.reemplazar_color(
            self.image_hsv,
            mask,
            self.target_hsv,
            self.mix_var.get(),
            self.keep_v_var.get(),
        )
        if self.result_bgr is None:
            messagebox.showerror("Error", "No se pudo procesar la imagen.")
            return
        self.show_image(self.result_bgr)
        self.status.config(text=f"Procesado | Objetivo HSV: {self.picked_hsv} | Destino HSV: {self.target_hsv}")

    # Genera y muestra una preview de selección (antes del reemplazo final).
    # Esto sirve para que el usuario vea si la máscara está bien ajustada con los sliders.
    #
    # Internamente:
    # - crea máscara con `logic.crear_mascara_hsv`
    # - genera preview con `logic.crear_vista_previa`
    # - muestra la preview
    def _show_selection_preview(self):
        if self.image_bgr is None:
            return
        mask = logic.crear_mascara_hsv(
            self.image_hsv,
            self.picked_hsv,
            self.tol_var.get(),
            self.blur_var.get(),
            self.morph_var.get(),
        )
        preview = logic.crear_vista_previa(self.image_bgr, mask)
        if preview is None:
            return
        self.show_image(preview)

    # Muestra una imagen BGR (OpenCV) en el canvas.
    # Conversión necesaria:
    # - OpenCV: BGR
    # - Pillow/Tkinter: RGB
    def show_image(self, bgr):
        if Image is None:
            return
        img = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img)
        self._show_on_canvas(pil_img)

    # Dibuja una imagen PIL en el canvas ajustándola al tamaño disponible.
    #
    # Qué hace:
    # - Calcula un `scale` para que la imagen quepa sin deformarse.
    # - Redimensiona la imagen.
    # - La centra en el canvas.
    # - Guarda `display_info` para poder mapear clicks del canvas a píxeles reales.
    def _show_on_canvas(self, pil_img):
        cw = max(self.canvas.winfo_width(), 1)
        ch = max(self.canvas.winfo_height(), 1)
        ow, oh = pil_img.size

        scale = min(cw / ow, ch / oh)
        dw = max(1, int(ow * scale))
        dh = max(1, int(oh * scale))
        resized = pil_img.resize((dw, dh), Image.LANCZOS)

        self.display_info = {
            "scale": scale,
            "x0": (cw - dw) // 2,
            "y0": (ch - dh) // 2,
            "dw": dw,
            "dh": dh,
            "ow": ow,
            "oh": oh,
        }

        self.tk_img = ImageTk.PhotoImage(resized)
        self.canvas.delete("all")
        self.canvas.create_image(self.display_info["x0"], self.display_info["y0"], image=self.tk_img, anchor=tk.NW)


    # Punto de entrada de la app.
    # - Crea la ventana principal de Tkinter.
    # - Instancia la clase de la aplicación.
    # - Inicia el loop de eventos (la app queda “escuchando” clicks/teclas/acciones).
if __name__ == "__main__":
    root = tk.Tk()
    app = ColorReplaceApp(root)
    root.mainloop()

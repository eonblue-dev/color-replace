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


class ColorReplaceApp:
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

    def _build_ui(self):
        self.left = tk.Frame(self.root, padx=10, pady=10)
        self.left.pack(side=tk.LEFT, fill=tk.Y)

        self.right = tk.Frame(self.root, padx=10, pady=10)
        self.right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        tk.Label(self.left, text="Carga y opciones", font=("Arial", 12, "bold")).pack(anchor="w")

        tk.Button(self.left, text="Cargar imagen", command=self.load_image).pack(fill=tk.X, pady=5)
        tk.Button(self.left, text="Ver original", command=self.show_original).pack(fill=tk.X, pady=5)

        tk.Label(self.left, text="Color objetivo").pack(anchor="w", pady=(10, 0))
        tk.Button(self.left, text="Seleccionar con click", command=self.enable_pick).pack(fill=tk.X, pady=5)

        tk.Label(self.left, text="Color destino").pack(anchor="w", pady=(10, 0))
        tk.Button(self.left, text="Elegir color destino...", command=self.choose_target_color).pack(fill=tk.X, pady=5)

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

    def show_original(self):
        if self.image_bgr is None:
            return
        self.show_image(self.image_bgr)
        self.status.config(text="Mostrando original")

    def enable_pick(self):
        self.pick_mode = True
        self.status.config(text="Click en la imagen para seleccionar color")

    def choose_target_color(self):
        color = colorchooser.askcolor(title="Selecciona color destino")
        if not color or color[0] is None:
            return
        r, g, b = [int(c) for c in color[0]]
        self.target_hsv = logic.to_hsv(r, g, b)
        self.status.config(text=f"Destino HSV: {self.target_hsv}")

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
        self.status.config(text=f"Color capturado HSV: {self.picked_hsv}")

    def process(self):
        if cv2 is None or np is None:
            messagebox.showerror("Error", "Faltan dependencias: cv2 o numpy.")
            return
        if self.image_hsv is None:
            messagebox.showwarning("Aviso", "Carga una imagen primero.")
            return
        if self.picked_hsv is None:
            messagebox.showwarning("Aviso", "Selecciona el color objetivo con click.")
            return

        mask = logic.mask(
            self.image_hsv,
            self.picked_hsv,
            self.tol_var.get(),
            self.blur_var.get(),
            self.morph_var.get(),
        )
        if mask is None:
            messagebox.showerror("Error", "No se pudo crear la mascara.")
            return

        self.result_bgr = logic.replace(
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
        self.status.config(text="Procesado")

    def _show_selection_preview(self):
        if self.image_bgr is None:
            return
        mask = logic.mask(
            self.image_hsv,
            self.picked_hsv,
            self.tol_var.get(),
            self.blur_var.get(),
            self.morph_var.get(),
        )
        preview = logic.preview(self.image_bgr, mask)
        if preview is None:
            return
        self.show_image(preview)

    def show_image(self, bgr):
        if Image is None:
            return
        img = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img)
        self._show_on_canvas(pil_img)

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

if __name__ == "__main__":
    root = tk.Tk()
    app = ColorReplaceApp(root)
    root.mainloop()

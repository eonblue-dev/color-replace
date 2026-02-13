try:
    import cv2
    import numpy as np
except Exception:
    cv2 = None
    np = None

import colorsys


# Convierte un color RGB (0..255) al formato HSV que usa OpenCV.
#
# ¿Por qué existe?
# - Tkinter (colorchooser) entrega colores en RGB (0..255).
# - OpenCV trabaja muy bien seleccionando y modificando colores en HSV, pero su HSV usa rangos:
#   - H: 0..179
#   - S: 0..255
#   - V: 0..255
#
# Qué hace paso a paso:
# 1) Asegura que r, g, b estén dentro de 0..255 (_clamp).
# 2) Si OpenCV está disponible, usa cv2.cvtColor para que el HSV calculado
#    coincida exactamente con el HSV que usa la imagen (evita desviaciones de tono).
# 3) Si OpenCV NO está disponible, usa colorsys (normaliza a 0..1 y reescala).
#
# Devuelve:
# - (h, s, v) en rangos OpenCV, listos para usarse en el resto del proyecto.
def convertir_rgb_a_hsv(r, g, b):
    # Convertir RGB (0-255) a HSV compatible con OpenCV (H 0-179, S/V 0-255).
    r_ok = _clamp(r)
    g_ok = _clamp(g)
    b_ok = _clamp(b)

    # Se prefiere la conversión de OpenCV cuando sea posible para evitar diferencias
    # entre implementaciones (por ejemplo, morado/cian que se ve más azulado/verdoso).
    if cv2 is not None and np is not None:
        bgr = np.uint8([[[b_ok, g_ok, r_ok]]])
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)[0, 0]
        return int(hsv[0]), int(hsv[1]), int(hsv[2])

    r_norm = r_ok / 255.0
    g_norm = g_ok / 255.0
    b_norm = b_ok / 255.0

    h, s, v = colorsys.rgb_to_hsv(r_norm, g_norm, b_norm)
    h_out = int(round(h * 179))
    s_out = int(round(s * 255))
    v_out = int(round(v * 255))
    return h_out, s_out, v_out


# Crea una máscara (0..255) que marca los píxeles similares a un color HSV objetivo.
#
# Entrada:
# - image_hsv: imagen completa en HSV (OpenCV)
# - color_hsv: (h, s, v) objetivo (por ejemplo, el pixel seleccionado con click)
# - tolerancia: cuánto “margen” permitimos alrededor del color objetivo
# - suavizado: tamaño del blur para suavizar bordes de la máscara
# - morph: iteraciones de limpieza morfológica (reduce ruido)
#
# Salida:
# - mask (2D, 0..255):
#   - 0  => no seleccionar
#   - 255 => seleccionar al máximo
#
# Pasos principales:
# 1) Calcula rangos min/max para H, S y V.
# 2) Usa cv2.inRange para seleccionar el rango.
# 3) Maneja el wrap-around del H (0..179) creando dos rangos si hace falta.
# 4) Suaviza con GaussianBlur (feather).
# 5) Limpia con morfología (open/close).
def crear_mascara_hsv(image_hsv, color_hsv, tolerancia, suavizado, morph):
    # Crear mascara HSV con tolerancia, suavizado y limpieza morfologica.
    if image_hsv is None or color_hsv is None or np is None or cv2 is None:
        return None

    hue, sat, val = color_hsv

    sat_min = max(sat - tolerancia, 0)
    sat_max = min(sat + tolerancia, 255)
    val_min = max(val - tolerancia, 0)
    val_max = min(val + tolerancia, 255)

    hue_min = hue - tolerancia
    hue_max = hue + tolerancia

    # Manejar el wrap-around del canal H (0-179).
    if hue_min < 0:
        lower1 = np.array([0, sat_min, val_min])
        upper1 = np.array([hue_max, sat_max, val_max])
        lower2 = np.array([179 + hue_min, sat_min, val_min])
        upper2 = np.array([179, sat_max, val_max])
        mask1 = cv2.inRange(image_hsv, lower1, upper1)
        mask2 = cv2.inRange(image_hsv, lower2, upper2)
        mask = mask1 | mask2
    elif hue_max > 179:
        lower1 = np.array([0, sat_min, val_min])
        upper1 = np.array([hue_max - 179, sat_max, val_max])
        lower2 = np.array([hue_min, sat_min, val_min])
        upper2 = np.array([179, sat_max, val_max])
        mask1 = cv2.inRange(image_hsv, lower1, upper1)
        mask2 = cv2.inRange(image_hsv, lower2, upper2)
        mask = mask1 | mask2
    else:
        lower = np.array([hue_min, sat_min, val_min])
        upper = np.array([hue_max, sat_max, val_max])
        mask = cv2.inRange(image_hsv, lower, upper)

    # Suavizado: kernel impar.
    if suavizado % 2 == 0:
        suavizado = suavizado + 1
    if suavizado > 1:
        mask = cv2.GaussianBlur(mask, (suavizado, suavizado), 0)

    # Morfologia para limpiar ruido.
    if morph > 0:
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=morph)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=morph)

    return mask


# Reemplaza el color en una imagen HSV usando una máscara como guía de “cuánto aplicar”.
#
# Entrada:
# - image_hsv: imagen HSV (OpenCV)
# - mask: máscara 0..255 (misma altura/ancho que image_hsv)
# - color_hsv: color destino (h, s, v) en rangos OpenCV
# - fuerza: 0..100 (intensidad del reemplazo)
# - mantener_brillo: si True, conserva el canal V original
#
# Idea:
# - Convertimos mask a un alpha 0..1.
# - Multiplicamos por fuerza para controlar la intensidad.
# - Mezclamos (blend) H y S hacia el color destino.
# - V se mantiene o también se mezcla según mantener_brillo.
#
# Devuelve:
# - Imagen BGR (lista para mostrar con OpenCV o convertir a RGB para UI).
def reemplazar_color(image_hsv, mask, color_hsv, fuerza, mantener_brillo):
    # Reemplazar H/S (y opcionalmente V) usando la mascara como mezcla.
    if image_hsv is None or mask is None or np is None or cv2 is None:
        return None

    alpha = mask.astype(np.float32) / 255.0
    alpha = alpha * (fuerza / 100.0)
    alpha = np.clip(alpha, 0.0, 1.0)

    hsv = image_hsv.astype(np.float32)
    hue_ch, sat_ch, val_ch = cv2.split(hsv)

    hue_t, sat_t, val_t = color_hsv

    hue_new = (1.0 - alpha) * hue_ch + alpha * hue_t
    sat_new = (1.0 - alpha) * sat_ch + alpha * sat_t

    if mantener_brillo:
        val_new = val_ch
    else:
        val_new = (1.0 - alpha) * val_ch + alpha * val_t

    hue_new = np.clip(hue_new, 0, 179).astype(np.uint8)
    sat_new = np.clip(sat_new, 0, 255).astype(np.uint8)
    val_new = np.clip(val_new, 0, 255).astype(np.uint8)

    hsv_new = cv2.merge([hue_new, sat_new, val_new])
    return cv2.cvtColor(hsv_new, cv2.COLOR_HSV2BGR)


# Genera una vista previa para ver la selección de la máscara (sin “procesar” definitivo).
#
# Qué hace:
# - Copia la imagen original.
# - Crea una imagen roja del mismo tamaño.
# - Convierte la máscara a alpha (0..1) y la hace más suave (multiplica por 0.45).
# - Mezcla base + rojo para resaltar la zona seleccionada.
#
# Devuelve:
# - Imagen BGR con la zona seleccionada marcada en rojo.
def crear_vista_previa(image_bgr, mask):
    # Generar una vista previa tintada para visualizar la seleccion.
    if image_bgr is None or mask is None or np is None:
        return None

    base = image_bgr.copy()
    tint = np.zeros_like(base)
    tint[:, :] = (0, 0, 255)

    alpha = mask.astype(np.float32) / 255.0
    alpha = alpha * 0.45
    alpha = alpha[:, :, None]

    base = base.astype(np.float32)
    tint = tint.astype(np.float32)

    preview = base * (1.0 - alpha) + tint * alpha
    return preview.astype(np.uint8)


# Helper: limita un valor al rango 0..255 y lo convierte a int.
#
# Se usa para evitar valores inválidos de canales de color.
def _clamp(value):
    return max(0, min(int(value), 255))

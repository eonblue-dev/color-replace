try:
    import cv2
    import numpy as np
except Exception:
    cv2 = None
    np = None

import colorsys


def to_hsv(r, g, b):
    # Convertir RGB (0-255) a HSV compatible con OpenCV (H 0-179, S/V 0-255).
    r_norm = _clamp(r) / 255.0
    g_norm = _clamp(g) / 255.0
    b_norm = _clamp(b) / 255.0
    h, s, v = colorsys.rgb_to_hsv(r_norm, g_norm, b_norm)
    return int(round(h * 179)), int(round(s * 255)), int(round(v * 255))


def mask(image_hsv, picked_hsv, tol, blur, morph):
    # Crear mascara HSV con tolerancia, suavizado y limpieza morfologica.
    if image_hsv is None or picked_hsv is None or np is None or cv2 is None:
        return None

    h, s, v = picked_hsv
    s_low = max(s - tol, 0)
    s_high = min(s + tol, 255)
    v_low = max(v - tol, 0)
    v_high = min(v + tol, 255)

    h_low = h - tol
    h_high = h + tol

    # Manejar el wrap-around del canal H (0-179) cuando la tolerancia cruza extremos.
    if h_low < 0:
        lower1 = np.array([0, s_low, v_low])
        upper1 = np.array([h_high, s_high, v_high])
        lower2 = np.array([179 + h_low, s_low, v_low])
        upper2 = np.array([179, s_high, v_high])
        mask = cv2.inRange(image_hsv, lower1, upper1) | cv2.inRange(image_hsv, lower2, upper2)
    elif h_high > 179:
        lower1 = np.array([0, s_low, v_low])
        upper1 = np.array([h_high - 179, s_high, v_high])
        lower2 = np.array([h_low, s_low, v_low])
        upper2 = np.array([179, s_high, v_high])
        mask = cv2.inRange(image_hsv, lower1, upper1) | cv2.inRange(image_hsv, lower2, upper2)
    else:
        lower = np.array([h_low, s_low, v_low])
        upper = np.array([h_high, s_high, v_high])
        mask = cv2.inRange(image_hsv, lower, upper)

    if blur % 2 == 0:
        blur += 1
    if blur > 1:
        mask = cv2.GaussianBlur(mask, (blur, blur), 0)

    if morph > 0:
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=morph)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=morph)

    return mask


def replace(image_hsv, mask, target_hsv, mix, keep_v):
    # Reemplazar H/S (y opcionalmente V) usando la mascara como alfa de mezcla.
    if image_hsv is None or mask is None or np is None or cv2 is None:
        return None

    alpha = (mask.astype(np.float32) / 255.0) * (mix / 100.0)
    alpha = np.clip(alpha, 0.0, 1.0)

    hsv = image_hsv.astype(np.float32)
    h_ch, s_ch, v_ch = cv2.split(hsv)

    target_h, target_s, target_v = target_hsv
    h_new = (1.0 - alpha) * h_ch + alpha * target_h
    s_new = (1.0 - alpha) * s_ch + alpha * target_s

    if keep_v:
        v_new = v_ch
    else:
        v_new = (1.0 - alpha) * v_ch + alpha * target_v

    hsv_new = cv2.merge([
        np.clip(h_new, 0, 179).astype(np.uint8),
        np.clip(s_new, 0, 255).astype(np.uint8),
        np.clip(v_new, 0, 255).astype(np.uint8),
    ])

    return cv2.cvtColor(hsv_new, cv2.COLOR_HSV2BGR)


def preview(image_bgr, mask):
    # Generar una vista previa tintada para visualizar la seleccion.
    if image_bgr is None or mask is None or np is None:
        return None

    overlay = image_bgr.copy()
    tint = np.zeros_like(overlay)
    tint[:, :] = (0, 0, 255)
    alpha = (mask.astype(np.float32) / 255.0) * 0.45
    alpha = alpha[:, :, None]
    preview = (overlay.astype(np.float32) * (1.0 - alpha) + tint.astype(np.float32) * alpha).astype(np.uint8)
    return preview


def _clamp(value):
    return max(0, min(int(value), 255))

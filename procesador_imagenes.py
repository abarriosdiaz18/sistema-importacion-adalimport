# ══════════════════════════════════════════════════════════════════════════════
# ADALIMPORT · procesador_imagenes.py  ·  v3.12 — Módulo Core (Diseño Perfecto)
# ══════════════════════════════════════════════════════════════════════════════
from __future__ import annotations
import io
import os
from typing import Optional, Tuple

try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
    PIL_DISPONIBLE = True
except ImportError:
    PIL_DISPONIBLE = False

try:
    from rembg import remove as _rembg_remove
    REMBG_DISPONIBLE = True
except ImportError:
    REMBG_DISPONIBLE = False

CANVAS_ML        = (1080, 1080)
CANVAS_IG_POST   = (1080, 1080)
CANVAS_IG_STORY  = (1080, 1920)

COLOR_FONDO_BLANCO  = (255, 255, 255, 255)
# Colores para el gradiente
COLOR_NAVY_DARK     = (5, 9, 15, 255)    
COLOR_NAVY_LIGHT    = (15, 28, 45, 255)  
COLOR_ORO           = (184, 150,  62)
# Badge Story
COLOR_ORO_BADGE     = (184, 150,  62) 
COLOR_WHITE_BADGE   = (255, 255, 255) 
COLOR_ORO_BADGE_FILL= (184, 150, 62, 10) 
COLOR_BLANCO        = (255, 255, 255)
COLOR_NEGRO         = (15,  15,  15)
COLOR_VERDE_NEON    = (0,   230, 118)

PADDING_PCT_ML      = 0.08
PADDING_PCT_RRSS    = 0.15

_FONT_PATHS_BOLD = [
    "C:\\Windows\\Fonts\\arialbd.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]
_FONT_PATHS_REGULAR = [
    "C:\\Windows\\Fonts\\arial.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]

def _cargar_fuente(tamaño: int, negrita: bool = False) -> "ImageFont.FreeTypeFont":
    rutas = _FONT_PATHS_BOLD if negrita else _FONT_PATHS_REGULAR
    for ruta in rutas:
        if os.path.isfile(ruta):
            try:
                return ImageFont.truetype(ruta, tamaño)
            except Exception:
                continue
    try:
        return ImageFont.load_default(size=tamaño)
    except TypeError:
        return ImageFont.load_default()

def _imagen_desde_bytes(datos: bytes) -> "Image.Image":
    img = Image.open(io.BytesIO(datos))
    if img.mode != "RGBA": img = img.convert("RGBA")
    return img

def _remover_fondo(img_rgba: "Image.Image") -> "Image.Image":
    if not REMBG_DISPONIBLE: return img_rgba
    _buf_in = io.BytesIO()
    img_rgba.save(_buf_in, format="PNG")
    _buf_in.seek(0)
    _bytes_out = _rembg_remove(_buf_in.read())
    return Image.open(io.BytesIO(_bytes_out)).convert("RGBA")

def _escalar_producto(img_rgba: "Image.Image", area_util: Tuple[int, int]) -> "Image.Image":
    return ImageOps.contain(img_rgba, area_util, Image.LANCZOS)

def _imagen_a_bytes(img: "Image.Image", formato: str = "PNG") -> bytes:
    buffer = io.BytesIO()
    img.save(buffer, format=formato, optimize=True)
    buffer.seek(0)
    return buffer.getvalue()

def _crear_fondo_gradiente(width: int, height: int) -> "Image.Image":
    base = Image.new('RGBA', (width, height), COLOR_NAVY_DARK)
    top = Image.new('RGBA', (width, height), COLOR_NAVY_LIGHT)
    mask = Image.new('L', (width, height))
    mask_data = []
    for y in range(height):
        alpha = int(255 * (1 - (y / height)))
        mask_data.extend([alpha] * width)
    mask.putdata(mask_data)
    base.paste(top, (0, 0), mask)
    return base

def _medir_texto(texto: str, fuente, draw) -> Tuple[int, int]:
    try:
        if hasattr(draw, "textbbox"):
            bbox = draw.textbbox((0, 0), texto, font=fuente)
            return (bbox[2] - bbox[0], bbox[3] - bbox[1])
        else:
            return draw.textsize(texto, font=fuente)
    except Exception:
        return (len(texto) * 15, 40) 

def _truncar_texto_inteligente(texto: str, max_chars: int = 60) -> str:
    if len(texto) <= max_chars:
        return texto
    recorte = texto[:max_chars]
    ultimo_espacio = recorte.rfind(" ")
    if ultimo_espacio != -1:
        return recorte[:ultimo_espacio] + "..."
    return recorte + "..."

def _wrap_text(texto: str, fuente, ancho_max_px: int, draw) -> list[str]:
    palabras = texto.split()
    lineas, linea_actual = [], ""
    for palabra in palabras:
        candidato = (linea_actual + " " + palabra).strip()
        ancho = _medir_texto(candidato, fuente, draw)[0]
        if ancho <= ancho_max_px:
            linea_actual = candidato
        else:
            if linea_actual: lineas.append(linea_actual)
            linea_actual = palabra
            if len(lineas) >= 4: break
    if linea_actual: lineas.append(linea_actual)
    if len(lineas) > 4:
        lineas = lineas[:4]
        lineas[-1] = lineas[-1].rstrip() + "..."
    return lineas

def _dibujar_logo_adalimport(draw, canvas_w: int, canvas_h: int, y_pos: int = 42, centrado: bool = False, margen_izq: int = 60) -> None:
    tamaño_fuente = max(32, canvas_w // 22)
    fuente = _cargar_fuente(tamaño_fuente, negrita=True)
    texto = "ADALIMPORT"
    if centrado:
        ancho_txt = _medir_texto(texto, fuente, draw)[0]
        x_pos = (canvas_w - ancho_txt) // 2
    else:
        x_pos = margen_izq 
        
    draw.text((x_pos + 2, y_pos + 2), texto, font=fuente, fill=(0, 0, 0, 160))
    draw.text((x_pos, y_pos), texto, font=fuente, fill=COLOR_ORO)

def _dibujar_nombre_producto(draw, nombre: str, canvas_w: int, y_inicio: int, margen_lateral: int = 80) -> int:
    nombre_limpio = _truncar_texto_inteligente(nombre, max_chars=60)
    ancho_max = canvas_w - (margen_lateral * 2)
    tamaño_fuente = max(34, canvas_w // 24)
    fuente = _cargar_fuente(tamaño_fuente, negrita=True)
    interlineado = int(tamaño_fuente * 0.45) 
    
    lineas = _wrap_text(nombre_limpio.upper(), fuente, ancho_max, draw)
    y_actual = y_inicio
    for linea in lineas:
        ancho_linea, alto_linea = _medir_texto(linea, fuente, draw)
        x = (canvas_w - ancho_linea) // 2
        draw.text((x + 2, y_actual + 2), linea, font=fuente, fill=(0, 0, 0, 200))
        draw.text((x, y_actual), linea, font=fuente, fill=COLOR_BLANCO)
        y_actual += alto_linea + interlineado
    return y_actual

def _dibujar_badge_precio_premium(draw, canvas, precio: float, posicion: str = "bottom_right", margen: int = 60, canvas_h: int = 1920) -> None:
    texto_precio = f"${precio:,.2f}"
    tamaño_fuente = max(30, canvas.width // 18) 
    fuente = _cargar_fuente(tamaño_fuente, negrita=True)
    ancho_txt, alto_txt = _medir_texto(texto_precio, fuente, draw)
    
    pad_h, pad_v = int(tamaño_fuente * 0.4), int(tamaño_fuente * 0.15)
    badge_w, badge_h = ancho_txt + pad_h * 2, alto_txt + pad_v * 2

    badge_x, badge_y = (canvas.width - badge_w) // 2, canvas_h - badge_h - (margen + 30)

    draw.rounded_rectangle([(badge_x, badge_y), (badge_x + badge_w, badge_y + badge_h)], radius=badge_h // 2, fill=COLOR_ORO_BADGE_FILL, outline=COLOR_ORO_BADGE, width=2)
    txt_x, txt_y = badge_x + (badge_w - ancho_txt) // 2, badge_y + (badge_h - alto_txt) // 2
    
    draw.text((txt_x + 1, txt_y + 1), texto_precio, font=fuente, fill=(0, 0, 0, 180))
    draw.text((txt_x, txt_y), texto_precio, font=fuente, fill=COLOR_WHITE_BADGE)

def _dibujar_badge_precio_ml(draw, canvas, precio: float, posicion: str = "bottom_right", margen: int = 50) -> None:
    texto_precio = f"${precio:,.2f}"
    tamaño_fuente = max(52, canvas.width // 12)
    fuente = _cargar_fuente(tamaño_fuente, negrita=True)
    ancho_txt, alto_txt = _medir_texto(texto_precio, fuente, draw)
    pad_h, pad_v = int(tamaño_fuente * 0.5), int(tamaño_fuente * 0.25)
    badge_w, badge_h = ancho_txt + pad_h * 2, alto_txt + pad_v * 2

    if posicion == "bottom_center":
        badge_x, badge_y = (canvas.width - badge_w) // 2, canvas.height - badge_h - margen
    else:
        badge_x, badge_y = canvas.width - badge_w - margen, canvas.height - badge_h - margen

    draw.rounded_rectangle([(badge_x, badge_y), (badge_x + badge_w, badge_y + badge_h)], radius=badge_h // 2, fill=COLOR_VERDE_NEON)
    txt_x, txt_y = badge_x + (badge_w - ancho_txt) // 2, badge_y + (badge_h - alto_txt) // 2
    draw.text((txt_x + 2, txt_y + 2), texto_precio, font=fuente, fill=(0, 100, 50, 150))
    draw.text((txt_x, txt_y), texto_precio, font=fuente, fill=COLOR_NEGRO)

def _componer_sobre_blanco(img_rgba: "Image.Image", tamaño: tuple) -> "Image.Image":
    ancho_obj, alto_obj = tamaño
    padding = int(min(ancho_obj, alto_obj) * PADDING_PCT_ML)
    area_util = (ancho_obj - padding * 2, alto_obj - padding * 2)
    img_escalada = ImageOps.contain(img_rgba, area_util, Image.LANCZOS)
    canvas = Image.new("RGBA", tamaño, COLOR_FONDO_BLANCO)
    offset_x, offset_y = (ancho_obj - img_escalada.width) // 2, (alto_obj - img_escalada.height) // 2
    
    temp_layer = Image.new('RGBA', tamaño, (0, 0, 0, 0))
    temp_layer.paste(img_escalada, (offset_x, offset_y))
    return Image.alpha_composite(canvas, temp_layer).convert("RGB")

def procesar_version_catalogo(datos_imagen: bytes) -> Optional[bytes]:
    if not PIL_DISPONIBLE: return None
    img_rgba = _imagen_desde_bytes(datos_imagen)
    img_sin_fondo = _remover_fondo(img_rgba)
    catalogo = _componer_sobre_blanco(img_sin_fondo, CANVAS_ML)
    return _imagen_a_bytes(catalogo, "PNG")

def procesar_version_ig_post(datos_imagen: bytes, precio: float, nombre: str) -> Optional[bytes]:
    if not PIL_DISPONIBLE: return None
    w, h = CANVAS_IG_POST
    img_rgba = _imagen_desde_bytes(datos_imagen)
    img_sin_fondo = _remover_fondo(img_rgba)
    
    canvas = _crear_fondo_gradiente(w, h)
    
    padding = int(min(w, h) * PADDING_PCT_RRSS)
    espacio_texto = int(h * 0.23) 
    area_util = (w - padding * 2, h - padding * 2 - espacio_texto)
    producto = _escalar_producto(img_sin_fondo, area_util)
    
    y_linea = h - espacio_texto - 5
    
    # FIX v3.12: Centrado perfecto en el lienzo disponible superior (entre el borde top y la línea)
    offset_x = (w - producto.width) // 2
    offset_y = (y_linea - producto.height) // 2 
    
    temp_layer = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    temp_layer.paste(producto, (offset_x, offset_y))
    canvas = Image.alpha_composite(canvas, temp_layer)
    
    try:
        draw = ImageDraw.Draw(canvas)
        _dibujar_logo_adalimport(draw, w, h)
        draw.line([(padding, y_linea), (w - padding, y_linea)], fill=(184, 150, 62, 120), width=2)
        _dibujar_nombre_producto(draw, nombre, w, h - espacio_texto + 25, margen_lateral=50)
    except Exception as e:
        print(f"Branding omitido: {e}")

    return _imagen_a_bytes(canvas.convert("RGB"), "JPEG")

def procesar_version_ig_story(datos_imagen: bytes, precio: float, nombre: str) -> Optional[bytes]:
    if not PIL_DISPONIBLE: return None
    w, h = CANVAS_IG_STORY
    img_rgba = _imagen_desde_bytes(datos_imagen)
    img_sin_fondo = _remover_fondo(img_rgba)
    
    canvas = _crear_fondo_gradiente(w, h)
    
    zona_header_h, zona_producto_h = int(h * 0.25), int(h * 0.45) 
    zona_precio_h = h - zona_header_h - zona_producto_h
    padding = int(w * PADDING_PCT_RRSS)
    area_util = (w - padding * 2, zona_producto_h - padding)
    producto = _escalar_producto(img_sin_fondo, area_util)
    
    offset_x = (w - producto.width) // 2
    offset_y = zona_header_h + (zona_producto_h - producto.height) // 2
    
    temp_layer = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    temp_layer.paste(producto, (offset_x, offset_y))
    canvas = Image.alpha_composite(canvas, temp_layer)
    
    try:
        draw = ImageDraw.Draw(canvas)
        _dibujar_logo_adalimport(draw, w, h, y_pos=80, margen_izq=80) 
        _dibujar_nombre_producto(draw, nombre, w, 340, margen_lateral=60)
        
        y_sep1, y_sep2 = zona_header_h, zona_header_h + zona_producto_h
        draw.line([(w*0.3, y_sep1), (w*0.7, y_sep1)], fill=(184, 150, 62, 40), width=2) 
        draw.line([(w*0.3, y_sep2), (w*0.7, y_sep2)], fill=(184, 150, 62, 40), width=2) 
        
        _dibujar_badge_precio_premium(draw, canvas, precio, posicion="bottom_center", margen=int(zona_precio_h * 0.35), canvas_h=h) 
    except Exception as e:
        print(f"Branding omitido: {e}")

    return _imagen_a_bytes(canvas.convert("RGB"), "JPEG")

def modulo_disponible() -> bool: return PIL_DISPONIBLE
def rembg_disponible() -> bool: return REMBG_DISPONIBLE
def version_info() -> dict: return {}
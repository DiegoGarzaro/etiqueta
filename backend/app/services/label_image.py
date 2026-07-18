"""Render location labels as 1-bit PNGs for the SLP650 thermal printer.

Design rules (SDK ``docs/11_INTEGRATION_GUIDE.md``): pure black on white,
no grays and no strokes thinner than 3 px; threshold instead of dithering.
The canvas targets the loaded SLP-NWB badge roll (``MediaBadge``): 750x567 px
at 300 dpi, landscape, x = feed direction.
"""

from io import BytesIO
from pathlib import Path

import qrcode
from PIL import Image, ImageDraw, ImageFont
from qrcode.constants import ERROR_CORRECT_M

from app.models.location import LocationType

_FONT_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"

MEDIA_BADGE_CANVAS = (750, 567)
"""Pixel canvas of the loaded MediaBadge roll at 300 dpi (width, height)."""

TYPE_LABELS: dict[LocationType, str] = {
    LocationType.COMODO: "Cômodo",
    LocationType.ARMARIO: "Armário",
    LocationType.GAVETA: "Gaveta",
    LocationType.PRATELEIRA: "Prateleira",
    LocationType.CAIXA: "Caixa",
    LocationType.ORGANIZADOR: "Organizador",
}

_MARGIN = 36
_RULE_HEIGHT = 5
_QR_TARGET = 300


def render_location_label(
    full_code: str,
    name: str,
    type_: LocationType,
    qr_url: str,
    canvas: tuple[int, int] = MEDIA_BADGE_CANVAS,
) -> bytes:
    """Render a location label ("Etiqueta" style) as a 1-bit PNG.

    Layout: the full code as a large header, a rule, then a QR code that opens
    the location in the app, with the name and type beside it.

    Args:
        full_code (str): Joined location code, e.g. ``"ARM-A · GAV-02"``.
        name (str): Location name.
        type_ (LocationType): Location type, printed as its Portuguese label.
        qr_url (str): URL encoded in the QR code.
        canvas (tuple[int, int]): Target canvas in pixels (width, height).

    Returns:
        bytes: PNG bytes of the rendered 1-bit label.
    """
    width, height = canvas
    image = Image.new("L", canvas, 255)
    draw = ImageDraw.Draw(image)
    content_width = width - 2 * _MARGIN

    # Header: the location code, bold, fitted to width.
    code_size = _fit_size(draw, full_code, content_width, max_size=120, min_size=36, bold=True)
    code_font = _font(code_size, bold=True)
    code_bbox = draw.textbbox((0, 0), full_code, font=code_font)
    code_height = code_bbox[3] - code_bbox[1]
    draw.text((width // 2, _MARGIN), full_code, font=code_font, fill=0, anchor="ma")

    rule_y = _MARGIN + code_height + 26
    draw.rectangle((_MARGIN, rule_y, width - _MARGIN, rule_y + _RULE_HEIGHT), fill=0)

    # Body: QR on the left, name and type on the right, both centered vertically.
    body_top = rule_y + _RULE_HEIGHT + 24
    body_height = height - _MARGIN - body_top
    qr_size = min(_QR_TARGET, body_height)
    qr = _qr_image(qr_url, qr_size)
    image.paste(qr, (_MARGIN, body_top + (body_height - qr.height) // 2))

    text_left = _MARGIN + qr.width + 28
    text_width = width - _MARGIN - text_left
    body_center = body_top + body_height // 2

    lines = _wrap_name(draw, name, text_width)
    name_size = min(
        _fit_size(draw, line, text_width, max_size=72, min_size=24, bold=True) for line in lines
    )
    name_font = _font(name_size, bold=True)
    line_height = name_size + 10
    type_size = 30
    block_height = len(lines) * line_height + type_size + 14
    y = body_center - block_height // 2
    for line in lines:
        draw.text((text_left, y), line, font=name_font, fill=0, anchor="la")
        y += line_height
    draw.text((text_left, y + 14), TYPE_LABELS[type_], font=_font(type_size), fill=0, anchor="la")

    # Threshold (no dithering): antialiased text edges snap to pure black/white.
    mono = image.convert("1", dither=Image.Dither.NONE)
    buffer = BytesIO()
    mono.save(buffer, "PNG")
    return buffer.getvalue()


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Return the bundled DejaVu Sans font at a given size.

    Args:
        size (int): Font size in pixels.
        bold (bool): Use the bold face.

    Returns:
        ImageFont.FreeTypeFont: The loaded font.
    """
    filename = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(_FONT_DIR / filename, size=size)


def _fit_size(
    draw: ImageDraw.ImageDraw,
    text: str,
    max_width: int,
    max_size: int,
    min_size: int,
    bold: bool = False,
) -> int:
    """Find the largest font size at which ``text`` fits ``max_width``.

    Args:
        draw (ImageDraw.ImageDraw): Draw context used for measuring.
        text (str): Text to measure.
        max_width (int): Available width in pixels.
        max_size (int): Upper bound for the font size.
        min_size (int): Lower bound for the font size.
        bold (bool): Measure with the bold face.

    Returns:
        int: The chosen font size (never below ``min_size``).
    """
    for size in range(max_size, min_size, -2):
        bbox = draw.textbbox((0, 0), text, font=_font(size, bold=bold))
        if bbox[2] - bbox[0] <= max_width:
            return size
    return min_size


def _wrap_name(draw: ImageDraw.ImageDraw, name: str, max_width: int) -> list[str]:
    """Split a long name into at most two lines for the label body.

    Args:
        draw (ImageDraw.ImageDraw): Draw context used for measuring.
        name (str): The location name.
        max_width (int): Available width in pixels.

    Returns:
        list[str]: One or two lines of text.
    """
    words = name.split()
    if len(words) < 2 or _fit_size(draw, name, max_width, max_size=72, min_size=40, bold=True) > 40:
        return [name]
    # Split at the space closest to the middle of the string.
    middle = len(name) // 2
    split = min(
        range(1, len(words)),
        key=lambda i: abs(len(" ".join(words[:i])) - middle),
    )
    return [" ".join(words[:split]), " ".join(words[split:])]


def _qr_image(data: str, target_size: int) -> Image.Image:
    """Render a QR code sized close to ``target_size`` with crisp modules.

    Args:
        data (str): Payload to encode.
        target_size (int): Desired edge length in pixels.

    Returns:
        Image.Image: A grayscale QR image with modules of at least 4 px.
    """
    qr = qrcode.QRCode(error_correction=ERROR_CORRECT_M, border=2, box_size=1)
    qr.add_data(data)
    qr.make(fit=True)
    modules = qr.modules_count + 2 * qr.border
    qr.box_size = max(4, target_size // modules)
    return qr.make_image(fill_color="black", back_color="white").get_image().convert("L")

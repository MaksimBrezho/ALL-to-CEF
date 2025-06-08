from colorsys import rgb_to_hls, hls_to_rgb

try:
    import matplotlib.colors as mcolors
except Exception:  # pragma: no cover - optional dependency
    mcolors = None

def hex_to_rgb(hex_color):
    if mcolors:
        return mcolors.to_rgb(hex_color)
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16)/255 for i in (0, 2, 4))

def rgb_to_hex(rgb_tuple):
    return '#{:02x}{:02x}{:02x}'.format(
        int(rgb_tuple[0] * 255),
        int(rgb_tuple[1] * 255),
        int(rgb_tuple[2] * 255)
    )

def get_shaded_color(base_hex: str, index: int, total: int) -> str:
    rgb = hex_to_rgb(base_hex)
    h, l, s = rgb_to_hls(*rgb)

    # Диапазон яркости: от 0.35 до 0.75
    l_min, l_max = 0.35, 0.75
    new_l = l_min + (index / max(1, total - 1)) * (l_max - l_min)

    shaded_rgb = hls_to_rgb(h, new_l, s)
    return rgb_to_hex(shaded_rgb)


def adjust_lightness(base_hex: str, factor: float) -> str:
    """Lighten or darken a color by multiplying its lightness."""
    rgb = hex_to_rgb(base_hex)
    h, l, s = rgb_to_hls(*rgb)
    l = max(0.0, min(1.0, l * factor))
    return rgb_to_hex(hls_to_rgb(h, l, s))


def generate_distinct_colors(n):
    import colorsys
    hues = [i / n for i in range(n)]
    colors = [colorsys.hsv_to_rgb(h, 0.6, 0.9) for h in hues]
    return ['#{:02x}{:02x}{:02x}'.format(int(r*255), int(g*255), int(b*255)) for r, g, b in colors]

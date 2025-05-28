def html_color(color):
    if isinstance(color, str):
        return color
    elif len(color) == 3:
        return f"rgb({color[0]:.3f}, {color[1]:.3f}, {color[2]:.3f})"
    elif len(color) == 4:
        return f"rgba({color[0]:.3f}, {color[1]:.3f}, {color[2]:.3f}, {color[3]:.3f})"

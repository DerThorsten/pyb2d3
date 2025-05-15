def html_color(color):
    if isinstance(color, str):
        return color
    elif len(color) == 3:
        return f"rgb({color[0]}, {color[1]}, {color[2]})"
    elif len(color) == 4:
        return f"rgba({color[0]}, {color[1]}, {color[2]}, {color[3]})"

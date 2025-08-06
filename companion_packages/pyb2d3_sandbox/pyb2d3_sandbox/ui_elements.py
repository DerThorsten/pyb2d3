class FloatSlider:
    def __init__(self, name, min_value, max_value, step, value, callback):
        self.name = name
        self.min_value = min_value
        self.max_value = max_value
        self.step = step
        self.value = value
        self.callback = callback


class Checkbox:
    def __init__(self, name, value, callback):
        self.name = name
        self.value = value
        self.callback = callback


class Button:
    def __init__(self, name, callback):
        self.name = name
        self.callback = callback


class Dropdown:
    def __init__(self, name, options, value, callback):
        self.name = name
        self.options = options
        self.value = value
        self.callback = callback


class RadioButtons:
    def __init__(self, name, options, value, callback):
        self.name = name
        self.options = options
        self.value = value
        self.callback = callback

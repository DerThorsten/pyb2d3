class FloatSlider:
    def __init__(self, label, min_value, max_value, step, value, callback):
        self.label = label
        self.min_value = min_value
        self.max_value = max_value
        self.step = step
        self.value = value
        self.callback = callback


class IntSlider:
    def __init__(self, label, min_value, max_value, step, value, callback):
        self.label = label
        self.min_value = min_value
        self.max_value = max_value
        self.step = step
        self.value = value
        self.callback = callback


class Checkbox:
    def __init__(self, label, value, callback):
        self.label = label
        self.value = value
        self.callback = callback


class Button:
    def __init__(self, label, callback):
        self.label = label
        self.callback = callback


class Dropdown:
    def __init__(self, label, options, value, callback):
        self.label = label
        self.options = options
        self.value = value
        self.callback = callback


class RadioButtons:
    def __init__(self, label, options, value, callback):
        self.label = label
        self.options = options
        self.value = value
        self.callback = callback

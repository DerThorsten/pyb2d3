import anywidget
import traitlets

# Output widgets from ipywidgets
from pathlib import Path
import sys

THIS_DIR = Path(__file__).resolve().parent
CANVAS_WIDGET_JS = THIS_DIR / "canvas_widget.js"
CANVAS_WIDGET_CSS = THIS_DIR / "canvas_widget.css"


class CanvasWidget(anywidget.AnyWidget):
    _esm = CANVAS_WIDGET_JS
    _tag_name = "canvas"
    # _css = CANVAS_WIDGET_CS
    _width = traitlets.Int(800).tag(sync=True)
    _height = traitlets.Int(600).tag(sync=True)
    _frame = traitlets.Int(0).tag(sync=True)

    def __init__(self, width, height, output_widget, **kwargs):
        super().__init__(_width=width, _height=height, **kwargs)
        self.on_msg(self._handle_custom_msg)
        self.output_widget = output_widget
        self.width = width
        self.height = height

        self.on_mouse_wheel = None
        self.on_mouse_click = None
        self.on_mouse_move = None
        self.on_mouse_down = None
        self.on_mouse_up = None

    def send_data(self, data):
        # send a custom message to the frontend
        # this will be a single numpy array
        self.send(data)

    def _handle_custom_msg(self, data, buffers):
        # handle incoming messages from the frontend
        # this is where you can process the data sent from the frontend

        # with self.output_widget:
        msg_type = data[0]
        # print("Received message :", data)
        if msg_type == "mouse_click":
            pass
        elif msg_type == "mouse_enter":
            if self.on_mouse_enter is not None:
                self.on_mouse_enter()
        elif msg_type == "mouse_leave":
            if self.on_mouse_leave is not None:
                self.on_mouse_leave()
        elif msg_type == "mouse_wheel":
            if self.on_mouse_wheel is not None:
                self.on_mouse_wheel(*data[1:])
        elif msg_type == "mouse_move":
            if self.on_mouse_move is not None:
                self.on_mouse_move(*data[1:])
        elif msg_type == "mouse_down":
            if self.on_mouse_down is not None:
                self.on_mouse_down(*data[1:])
        elif msg_type == "mouse_up":
            if self.on_mouse_up is not None:
                self.on_mouse_up(*data[1:])
        elif msg_type == "click":
            if self.on_mouse_click is not None:
                self.on_mouse_click(*data[1:])
        else:
            print(f"Unknown message type: {msg_type}", file=sys.stderr)
            print(f"Data: {data}", file=sys.stderr)

import anywidget
import traitlets
import pyjs
from IPython.display import display
import numpy as np
import random
import string
# print exceptions tracebacks in the browser console


def _rand_name():
    """Generate a random name for the canvas."""
    # Generate a random string of length 8
    return "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))


class OffscreenCanvas(anywidget.AnyWidget):
    _esm = """
        function render({ model, el }) {

        const _name = () => model.get("_name");
        console.log("Canvas name: ", _name());

        const _canvas_name = () => `_canvas_${_name()}`;
        const _reciver_name = () => `_canvas_reciver_${_name()}`;

        let canvas = document.createElement("canvas");

        const width = model.get("width");
        if(width <= 1.00001) {
            canvas.width = window.innerWidth * width;
        } else {
            canvas.width = Math.round(width);
        }
        const height = model.get("height");
        if(height <= 1.00001) {
            canvas.height = window.innerHeight * height;
        } else {
            canvas.height = Math.round(height);
        }

        canvas.style.width = "100%";
        canvas.style.height = "100%";

        const offscreen = canvas.transferControlToOffscreen();


        function sendMouseEvent(event) {

            const rect = canvas.getBoundingClientRect();
            const scaleX = canvas.width / rect.width;   // CSS → pixel ratio
            const scaleY = canvas.height / rect.height;
            try{
                globalThis.callGlobalReceiver(_reciver_name(), "on_mouse_events",
                    event.type,
                    (event.clientX - rect.left) * scaleX,
                    (event.clientY - rect.top) * scaleY,
                )
            }
            // we want to remove all event listeners if the reciver is not defined
            catch (e) {
                console.error("Error sending mouse event, removing listeners:", e);
                canvas.removeEventListener("mousedown", sendMouseEvent);
                canvas.removeEventListener("mouseup",   sendMouseEvent);
                canvas.removeEventListener("mousemove", sendMouseEvent);
                canvas.removeEventListener("mouseenter", sendMouseEvent);
                canvas.removeEventListener("mouseleave", sendMouseEvent);
            }

        }

        canvas.addEventListener("mousedown", sendMouseEvent);
        canvas.addEventListener("mouseup",   sendMouseEvent);
        canvas.addEventListener("mousemove", sendMouseEvent);
        canvas.addEventListener("mouseenter", sendMouseEvent);
        canvas.addEventListener("mouseleave", sendMouseEvent);


        canvas.addEventListener("wheel", (event) => {
            event.preventDefault();
            event.stopPropagation();
            globalThis.callGlobalReceiver(_reciver_name(), "on_wheel_event",
                event.deltaY
            )
        });

        // keyboard events
        async function sendKeyboardEvent(event) {
            event.preventDefault();
            event.stopPropagation();
            try {
                await globalThis.callGlobalReceiver(
                _receiver_name(),
                'on_keyboard_events',
                event.type,
                event.key,
                event.ctrlKey,
                event.shiftKey,
                event.metaKey
                );
            } catch (e) {
                // we want to remove all event listeners if the receiver is not defined
                console.error(
                'Error while sending keyboard event, removing listeners:',
                e
                );
                removeAllListeners();
            }
        }

        // keyboard events
        canvas.addEventListener('keydown', sendKeyboardEvent);
        canvas.addEventListener('keyup', sendKeyboardEvent);
        canvas.addEventListener('keypress', sendKeyboardEvent);

        async function storeAsGlobal() {
            console.log("Storing offscreen canvas as  global:", _canvas_name());
            await globalThis.storeAsGlobal(offscreen, _canvas_name());
            console.log("Stored offscreen canvas as global:", _canvas_name());
        }
        storeAsGlobal();

        model.on("change:_name", () => {
        });

        model.on("change:width", () => {
            if(model.get("width") <= 1.00001) {
                canvas.width = model.get("width") * window.innerWidth;
            } else {
                canvas.width = Math.round(model.get("width"));
            }
        });

        model.on("change:height", () => {
            if(model.get("height") <= 1.00001) {
                canvas.height = model.get("height") * window.innerHeight;
            } else {
                canvas.height = Math.round(model.get("height"));
            }
        });


        el.appendChild(canvas);
    }
	export default { render };
    """
    _css = """
    .widget-inline-hbox {
        width: 100%;
    }
    .widget-inline-vbox {
        width: 100%;
    }
    """
    _name = traitlets.Unicode().tag(sync=True)
    mouse_event = traitlets.Dict(default_value={}, allow_none=True).tag(sync=True)
    width = traitlets.Float(0.5).tag(sync=True)
    height = traitlets.Float(0.5).tag(sync=True)

    def __init__(self, *args, **kwargs):
        _name = _rand_name()
        self._reciver_name = f"_canvas_reciver_{_name}"
        self._canvas_name = f"_canvas_{_name}"

        # create a bunch of python function which will be wrapped in JS functions.
        # these are the callbacks that will be fired when the mouse events happen.

        self.arr_mouse_state = np.array([0, 0, 0, 0], dtype=np.uint32)  # [is_inside, is_down, x, y]

        self._js_receiver = pyjs.js.globalThis.Function(
            "arr",
            """return {
            arr_mouse_state : arr,
            on_wheel_event: function(deltaY) {
                if (this.on_wheel) {
                    this.on_wheel(deltaY);
                }
            },
            on_keyboard_events: function(event, key, ctrl, shift, meta){
                if( event == "keydown" ) {
                    if( this.on_key_down ) {
                        this.on_key_down(key, ctrl, shift, meta);
                    }
                }
                else if( event == "keyup" ) {
                    if( this.on_key_up ) {
                        this.on_key_up(key, ctrl, shift, meta);
                    }
                }
                else if( event == "keypress" ) {
                    if( this.on_key_press ) {
                        this.on_key_press(key, ctrl, shift, meta);
                    }
                }
            },
            on_mouse_events: function(event, x, y) {

                if (event === "mouseenter") {
                    this.arr_mouse_state[0] = 1;  // is_inside
                    this.arr_mouse_state[1] = 0;  // is_down

                    if (this.on_mouse_enter) {
                        this.on_mouse_enter(x, y);
                    }

                } else if (event === "mouseleave") {
                    this.arr_mouse_state[0] = 0;  // is_inside
                    this.arr_mouse_state[1] = 0;  // is_down

                    if (this.on_mouse_leave) {
                        this.on_mouse_leave(x, y);
                    }

                } else if (event === "mousedown") {
                    this.arr_mouse_state[1] = 1;  // is_down
                    if (this.on_mouse_down) {
                        this.on_mouse_down(x, y);
                    }

                } else if (event === "mouseup") {
                    this.arr_mouse_state[1] = 0;  // is_down
                    if (this.on_mouse_up) {
                        this.on_mouse_up(x, y);
                    }
                }
                else if (event === "mousemove") {
                    if (this.on_mouse_move) {
                        this.on_mouse_move(x, y);
                    }
                }
                // always update the mouse position
                this.arr_mouse_state[2] = x;  // x position
                this.arr_mouse_state[3] = y;  // y position
            },
            has_property: function(name) {
                return this.hasOwnProperty(name) && this[name] !== null;
            },
            add_to_cleanup : function(name) {
              this.cleanup_list.push(name);
            },
            cleanup_list : [],
            cleanup : function() {
                // list contains names on receiver where we need to call .delete()
                for (let i = 0; i < this.cleanup_list.length; i++) {
                    const name = this.cleanup_list[i];
                    const item = receiver[name];
                    item.delete();
                }
            },



        }""",
        )(pyjs.buffer_to_js_typed_array(self.arr_mouse_state, view=True))
        pyjs.js.globalThis[self._reciver_name] = self._js_receiver

        super().__init__(*args, _name=_name, **kwargs)

        self._canvas = None

    def __del__(self):
        super().__del__()

        """Cleanup the canvas when the object is deleted."""
        pyjs.js.Function(
            "reciver",
            "reciver_name",
            """
            if(recive._cleanup_mouse_enter) {
                reciver._cleanup_mouse_enter.delete();
            }
            if(reciver._cleanup_mouse_leave) {
                reciver._cleanup_mouse_leave.delete();
            }
            if(reciver._cleanup_mouse_down) {
                reciver._cleanup_mouse_down.delete();
            }
            if(reciver._cleanup_mouse_up) {
                reciver._cleanup_mouse_up.delete();
            }
            if(reciver._cleanup_mouse_move) {
                reciver._cleanup_mouse_move.delete();
            }
            delete globalThis[reciver_name];
        """,
        )(self._js_receiver, self._reciver_name)

    def _on_mouse_event(self, event_name, callback):
        """Helper function to set mouse event callbacks."""

        if isinstance(callback, pyjs.JsValue):
            self._js_receiver[f"on_{event_name}"] = callback
        else:
            js_callback, cleanup = pyjs.create_callable(callback)
            self._js_receiver[f"on_{event_name}"] = js_callback
            setattr(self._js_receiver, f"_cleanup_{event_name}", cleanup)

    def on_mouse_enter(self, callback):
        self._on_mouse_event("mouse_enter", callback)

    def on_mouse_out(self, callback):
        self.on_mouse_leave(callback)

    def on_mouse_wheel(self, callback):
        event_name = "wheel"
        if isinstance(callback, pyjs.JsValue):
            self._js_receiver[f"on_{event_name}"] = callback
        else:
            js_callback, cleanup = pyjs.create_callable(callback)
            self._js_receiver[f"on_{event_name}"] = js_callback
            setattr(self._js_receiver, f"_cleanup_{event_name}", cleanup)

    def on_mouse_leave(self, callback):
        self._on_mouse_event("mouse_leave", callback)

    def on_mouse_down(self, callback):
        self._on_mouse_event("mouse_down", callback)

    def on_mouse_up(self, callback):
        self._on_mouse_event("mouse_up", callback)

    def on_mouse_move(self, callback):
        self._on_mouse_event("mouse_move", callback)

    # helper function to add a callback for an event an event
    def _on_event(self, event_name, callback):
        # for the offscreen canvas, we atm make the simplification that
        # only one callback can be set for each event.
        # This might change in the future, but for now it is sufficient.
        pyjs.js.console.log("_js_receiver:", self._js_receiver)
        if self._js_receiver.has_property(f"on_{event_name}"):
            raise RuntimeError(
                f"Event '{event_name}' already has a callback set. Only one callback is allowed per event for the OffscreenCanvasCore."
            )

        # if the callback is a js function, we can just set it directly.
        if isinstance(callback, pyjs.JsValue):
            self._js_receiver[f"on_{event_name}"] = callback

        # if the callback is a python function, we need to create a js callable.
        # since this callback needs to be deleted later, we need to store the cleanup function
        else:
            js_callback, cleanup = pyjs.create_callable(callback)
            self._js_receiver[f"on_{event_name}"] = js_callback
            cleanup_js_fname = f"_cleanup_{event_name}"
            setattr(self._js_receiver, cleanup_js_fname, cleanup)
            self._js_receiver.add_to_cleanup(cleanup_js_fname)

    def on_key_down(self, callback):
        self._on_event("key_down", callback)

    def on_key_up(self, callback):
        self._on_event("key_up", callback)

    def on_key_press(self, callback):
        self._on_event("key_press", callback)

    def is_displayed(self):
        """Check if the canvas is ready."""
        return self._canvas is not None

    async def _ready(self):
        jsf = pyjs.js.Function(f"""
            const ret =  typeof globalThis.{self._canvas_name} !== "undefined";
            // console.log("Canvas {self._canvas_name} ready? ", ret);
            return ret;
        """)

        make_sleep_fun = pyjs.js.Function("""

            async function js_sleep(waiting_time_ms) {

                await Promise.resolve();                     // let the event loop run
                await new Promise(r => setTimeout(r, waiting_time_ms)); // let other async work happen
                await new Promise(r => queueMicrotask(r));   // let microtasks run
            }
            return js_sleep;
        """)
        js_sleep = make_sleep_fun()

        c = 0
        factor = 2
        sleeping_time = 10
        while not jsf():
            await js_sleep(sleeping_time)
            sleeping_time = int(factor * sleeping_time)

            c += 1
            if c >= 15:
                pyjs.js.console.log(f"Canvas {self._canvas_name} was not created in time.")
                raise RuntimeError(f"Canvas {self._canvas_name} was not created in time.")

        self._canvas = pyjs.js.globalThis[self._canvas_name]

    def get_canvas(self):
        """Get the offscreen canvas element."""
        if self._canvas is None:
            raise RuntimeError(
                "Canvas is not displayed yet. Call await canvas.adisplay() to display the canvas."
            )
        return self._canvas

    async def adisplay(self):
        display(self)
        await self._ready()

    # mouse state
    def mouse_is_down(self):
        """Check if the mouse is currently pressed down."""
        return self.arr_mouse_state[1] == 1

    def mouse_is_inside(self):
        """Check if the mouse is currently inside the canvas."""
        return self.arr_mouse_state[0] == 1

    def mouse_position(self):
        """Get the current mouse position as a tuple (x, y)."""
        return (self.arr_mouse_state[2], self.arr_mouse_state[3])

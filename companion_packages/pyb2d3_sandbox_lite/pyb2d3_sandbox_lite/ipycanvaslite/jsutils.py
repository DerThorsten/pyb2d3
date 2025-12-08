import pyjs


def _py_list_like_to_js(value, cache):
    vid = id(value)
    if vid in cache:
        return cache[vid]
    j_value = pyjs.js_array()
    cache[vid] = j_value
    for v in value:
        js_v = to_js(v, cache=cache)
        j_value.push(js_v)
    return j_value


def _py_dict_like_to_js(value, cache):
    vid = id(value)
    if vid in cache:
        return cache[vid]
    j_value = pyjs.js_object()
    cache[vid] = j_value
    for k, v in value.items():
        if not isinstance(k, str):
            raise TypeError(f"Dictionary keys must be strings, got {type(k)}")
        js_v = to_js(v, cache=cache)
        j_value[k] = js_v
    return j_value


def _py_set_like_to_js(value, cache):
    vid = id(value)
    if vid in cache:
        return cache[vid]
    j_value = pyjs.new(pyjs.js.Set)
    cache[vid] = j_value
    for v in value:
        js_v = to_js(v, cache=cache)
        j_value.add(js_v)
    return j_value


# note that we assume dicts only have string keys!
# this is a feature! the original pyjs implementation does **not**
# assume this, but for  passing arround function arguments,
# we need this
def to_js(value, cache=None):
    """
    special converter that differes slightly from the original pyjs.
    dicts are converted to js objects, not maps !
    Furthermore, any class with an `as_js` method
    will be converted using that method.
    """
    if cache is None:
        cache = dict()

    if isinstance(value, pyjs.JsValue):
        return value
    elif isinstance(value, (list, tuple)):
        return _py_list_like_to_js(value=value, cache=cache)
    elif isinstance(value, dict):
        return _py_dict_like_to_js(value=value, cache=cache)
    elif isinstance(value, set):
        return _py_set_like_to_js(value=value, cache=cache)
    elif value is None:
        return pyjs.js_undefined()
    elif isinstance(value, (int, float, str, bool)):
        return pyjs.JsValue(value)
    # # bytestring
    elif isinstance(value, bytes):
        return pyjs.to_js(value)
    elif hasattr(value, "as_js"):
        return value._as_js()
    else:
        raise TypeError(f"Cannot convert {type(value)} to JavaScript object")


def exec_js_file(filename):
    """
    Evaluate a JavaScript file.
    """
    try:
        with open(filename, "r") as f:
            js_code = f.read()

        pyjs.js.Function(js_code)()
    except Exception as e:
        raise RuntimeError(f"Error executing JavaScript file {filename}: {e}") from e

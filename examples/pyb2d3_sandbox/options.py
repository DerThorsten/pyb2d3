"""Extra options for samples: name / value strings the launcher passes in (URL query
parameters in the browser, ``-o name=value`` natively), readable by any sample:

    text = get_extra_options().get("text", "pyb2d3")

A value ``b64:<base64url>`` is decoded (UTF-8), so a link need not show its text right
away (``encode_option`` makes one); anything else is used as is. The options hold for the
whole run (one namespace: use distinctive names).
"""

import base64

_PREFIX = "b64:"
_options = {}


def encode_option(text):
    """the encoded form of `text`: ``b64:`` + base64url without padding"""
    encoded = base64.urlsafe_b64encode(text.encode("utf-8")).decode("ascii")
    return _PREFIX + encoded.rstrip("=")


def decode_option(value):
    """`value` decoded if it is ``b64:...``, else as is"""
    if not value.startswith(_PREFIX):
        return value
    encoded = value[len(_PREFIX) :]
    return base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)).decode("utf-8")


def set_extra_options(options):
    """the options of this run (a mapping name -> string), replacing earlier ones"""
    _options.clear()
    _options.update({str(name): decode_option(str(value)) for name, value in options.items()})


def get_extra_options():
    """the options of this run (decoded), a copy"""
    return dict(_options)

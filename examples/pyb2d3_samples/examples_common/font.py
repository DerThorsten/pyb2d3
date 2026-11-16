"""Prebaked monospace pixel fonts: write text with blocks (balls, squares, letters, ...).

    cells, letters = text_blocks("Hello", font="5x7")   # block positions in grid units
    bodies = create_blocks(world, cells, origin=(-10, 0), size=0.4, shape="square")
    bodies = create_letters(world, cells, letters, origin=(-10, 0), size=0.4)       # rigid
    bodies = create_soft_letters(world, cells, letters, origin=(-10, 0), size=0.4)  # springs

    cells, letters = text_blocks(wrap_text(long_text, 20), "3x5", subdivision=2)   # 2x2 per pixel

Multiline text: '\\n' starts a new line (going down from the first one); wrap_text wraps.

A glyph is a tuple of row bitmasks, top row first; bit `width - 1` is the leftmost column.
"""

import textwrap
from dataclasses import dataclass

import numpy as np

import pyb2d3 as b2d


@dataclass(frozen=True)
class Font:
    width: int
    height: int
    glyphs: dict  # character -> rows (top first)

    def glyph(self, char):
        """the rows of `char`: the character, else its upper case form, else '?'"""
        return self.glyphs.get(char) or self.glyphs.get(char.upper()) or self.glyphs["?"]


# the classic 5 x 7 font of character LCDs
FONT_5X7 = Font(
    5,
    7,
    {
        " ": (0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00),
        "!": (0x04, 0x04, 0x04, 0x04, 0x00, 0x00, 0x04),
        '"': (0x0A, 0x0A, 0x0A, 0x00, 0x00, 0x00, 0x00),
        "#": (0x0A, 0x0A, 0x1F, 0x0A, 0x1F, 0x0A, 0x0A),
        "$": (0x04, 0x0F, 0x14, 0x0E, 0x05, 0x1E, 0x04),
        "%": (0x18, 0x19, 0x02, 0x04, 0x08, 0x13, 0x03),
        "&": (0x0C, 0x12, 0x14, 0x08, 0x15, 0x12, 0x0D),
        "'": (0x0C, 0x04, 0x08, 0x00, 0x00, 0x00, 0x00),
        "(": (0x02, 0x04, 0x08, 0x08, 0x08, 0x04, 0x02),
        ")": (0x08, 0x04, 0x02, 0x02, 0x02, 0x04, 0x08),
        "*": (0x00, 0x04, 0x15, 0x0E, 0x15, 0x04, 0x00),
        "+": (0x00, 0x04, 0x04, 0x1F, 0x04, 0x04, 0x00),
        ",": (0x00, 0x00, 0x00, 0x00, 0x0C, 0x04, 0x08),
        "-": (0x00, 0x00, 0x00, 0x1F, 0x00, 0x00, 0x00),
        ".": (0x00, 0x00, 0x00, 0x00, 0x00, 0x0C, 0x0C),
        "/": (0x00, 0x01, 0x02, 0x04, 0x08, 0x10, 0x00),
        "0": (0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E),
        "1": (0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E),
        "2": (0x0E, 0x11, 0x01, 0x02, 0x04, 0x08, 0x1F),
        "3": (0x1F, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0E),
        "4": (0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02),
        "5": (0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E),
        "6": (0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E),
        "7": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08),
        "8": (0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E),
        "9": (0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C),
        ":": (0x00, 0x0C, 0x0C, 0x00, 0x0C, 0x0C, 0x00),
        ";": (0x00, 0x0C, 0x0C, 0x00, 0x0C, 0x04, 0x08),
        "<": (0x02, 0x04, 0x08, 0x10, 0x08, 0x04, 0x02),
        "=": (0x00, 0x00, 0x1F, 0x00, 0x1F, 0x00, 0x00),
        ">": (0x08, 0x04, 0x02, 0x01, 0x02, 0x04, 0x08),
        "?": (0x0E, 0x11, 0x01, 0x02, 0x04, 0x00, 0x04),
        "@": (0x0E, 0x11, 0x01, 0x0D, 0x15, 0x15, 0x0E),
        "A": (0x0E, 0x11, 0x11, 0x11, 0x1F, 0x11, 0x11),
        "B": (0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E),
        "C": (0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E),
        "D": (0x1C, 0x12, 0x11, 0x11, 0x11, 0x12, 0x1C),
        "E": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F),
        "F": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10),
        "G": (0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0F),
        "H": (0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
        "I": (0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
        "J": (0x07, 0x02, 0x02, 0x02, 0x02, 0x12, 0x0C),
        "K": (0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11),
        "L": (0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F),
        "M": (0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11),
        "N": (0x11, 0x11, 0x19, 0x15, 0x13, 0x11, 0x11),
        "O": (0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
        "P": (0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10),
        "Q": (0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D),
        "R": (0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11),
        "S": (0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E),
        "T": (0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
        "U": (0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
        "V": (0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04),
        "W": (0x11, 0x11, 0x11, 0x15, 0x15, 0x15, 0x0A),
        "X": (0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11),
        "Y": (0x11, 0x11, 0x11, 0x0A, 0x04, 0x04, 0x04),
        "Z": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F),
        "[": (0x0E, 0x08, 0x08, 0x08, 0x08, 0x08, 0x0E),
        "]": (0x0E, 0x02, 0x02, 0x02, 0x02, 0x02, 0x0E),
        "_": (0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x1F),
        "a": (0x00, 0x00, 0x0E, 0x01, 0x0F, 0x11, 0x0F),
        "b": (0x10, 0x10, 0x16, 0x19, 0x11, 0x11, 0x1E),
        "c": (0x00, 0x00, 0x0E, 0x10, 0x10, 0x11, 0x0E),
        "d": (0x01, 0x01, 0x0D, 0x13, 0x11, 0x11, 0x0F),
        "e": (0x00, 0x00, 0x0E, 0x11, 0x1F, 0x10, 0x0E),
        "f": (0x06, 0x09, 0x08, 0x1C, 0x08, 0x08, 0x08),
        "g": (0x00, 0x0F, 0x11, 0x11, 0x0F, 0x01, 0x0E),
        "h": (0x10, 0x10, 0x16, 0x19, 0x11, 0x11, 0x11),
        "i": (0x04, 0x00, 0x0C, 0x04, 0x04, 0x04, 0x0E),
        "j": (0x02, 0x00, 0x06, 0x02, 0x02, 0x12, 0x0C),
        "k": (0x10, 0x10, 0x12, 0x14, 0x18, 0x14, 0x12),
        "l": (0x0C, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
        "m": (0x00, 0x00, 0x1A, 0x15, 0x15, 0x11, 0x11),
        "n": (0x00, 0x00, 0x16, 0x19, 0x11, 0x11, 0x11),
        "o": (0x00, 0x00, 0x0E, 0x11, 0x11, 0x11, 0x0E),
        "p": (0x00, 0x00, 0x1E, 0x11, 0x1E, 0x10, 0x10),
        "q": (0x00, 0x00, 0x0D, 0x13, 0x0F, 0x01, 0x01),
        "r": (0x00, 0x00, 0x16, 0x19, 0x10, 0x10, 0x10),
        "s": (0x00, 0x00, 0x0E, 0x10, 0x0E, 0x01, 0x1E),
        "t": (0x08, 0x08, 0x1C, 0x08, 0x08, 0x09, 0x06),
        "u": (0x00, 0x00, 0x11, 0x11, 0x11, 0x13, 0x0D),
        "v": (0x00, 0x00, 0x11, 0x11, 0x11, 0x0A, 0x04),
        "w": (0x00, 0x00, 0x11, 0x11, 0x15, 0x15, 0x0A),
        "x": (0x00, 0x00, 0x11, 0x0A, 0x04, 0x0A, 0x11),
        "y": (0x00, 0x00, 0x11, 0x11, 0x0F, 0x01, 0x0E),
        "z": (0x00, 0x00, 0x1F, 0x02, 0x04, 0x08, 0x1F),
    },
)

# a tiny blocky 3 x 5 font (lower case is drawn as upper case)
FONT_3X5 = Font(
    3,
    5,
    {
        " ": (0, 0, 0, 0, 0),
        "!": (2, 2, 2, 0, 2),
        '"': (5, 5, 0, 0, 0),
        "#": (5, 7, 5, 7, 5),
        "&": (2, 5, 2, 5, 3),
        "'": (2, 2, 0, 0, 0),
        "(": (1, 2, 2, 2, 1),
        ")": (4, 2, 2, 2, 4),
        "*": (0, 5, 2, 5, 0),
        "+": (0, 2, 7, 2, 0),
        ",": (0, 0, 0, 2, 4),
        "-": (0, 0, 7, 0, 0),
        ".": (0, 0, 0, 0, 2),
        "/": (1, 1, 2, 4, 4),
        "0": (7, 5, 5, 5, 7),
        "1": (2, 6, 2, 2, 7),
        "2": (6, 1, 2, 4, 7),
        "3": (6, 1, 2, 1, 6),
        "4": (5, 5, 7, 1, 1),
        "5": (7, 4, 6, 1, 6),
        "6": (3, 4, 7, 5, 7),
        "7": (7, 1, 1, 2, 2),
        "8": (7, 5, 7, 5, 7),
        "9": (7, 5, 7, 1, 6),
        ":": (0, 2, 0, 2, 0),
        ";": (0, 2, 0, 2, 4),
        "<": (1, 2, 4, 2, 1),
        "=": (0, 7, 0, 7, 0),
        ">": (4, 2, 1, 2, 4),
        "?": (6, 1, 2, 0, 2),
        "@": (2, 5, 7, 4, 3),
        "A": (2, 5, 7, 5, 5),
        "B": (6, 5, 6, 5, 6),
        "C": (3, 4, 4, 4, 3),
        "D": (6, 5, 5, 5, 6),
        "E": (7, 4, 6, 4, 7),
        "F": (7, 4, 6, 4, 4),
        "G": (3, 4, 5, 5, 3),
        "H": (5, 5, 7, 5, 5),
        "I": (7, 2, 2, 2, 7),
        "J": (1, 1, 1, 5, 2),
        "K": (5, 5, 6, 5, 5),
        "L": (4, 4, 4, 4, 7),
        "M": (5, 7, 7, 5, 5),
        "N": (6, 5, 5, 5, 5),
        "O": (2, 5, 5, 5, 2),
        "P": (6, 5, 6, 4, 4),
        "Q": (2, 5, 5, 6, 3),
        "R": (6, 5, 6, 5, 5),
        "S": (3, 4, 2, 1, 6),
        "T": (7, 2, 2, 2, 2),
        "U": (5, 5, 5, 5, 7),
        "V": (5, 5, 5, 5, 2),
        "W": (5, 5, 7, 7, 5),
        "X": (5, 5, 2, 5, 5),
        "Y": (5, 5, 2, 2, 2),
        "Z": (7, 1, 2, 4, 7),
        "_": (0, 0, 0, 0, 7),
    },
)

FONTS = {"5x7": FONT_5X7, "3x5": FONT_3X5}


def text_blocks(text, font="5x7", subdivision=1):
    """The blocks of `text`: (cells, letters). `cells` an (n, 2) int array of block positions
    in grid units (x right, y up; the origin is the lower left corner of the first line),
    `letters` the index in `text` of the character each block belongs to. Characters
    advance by the font width + 1, a new line ('\\n') by the font height + 2.
    `subdivision` n: every font pixel made of n x n blocks (cells in units of 1 / n pixel)."""
    f = FONTS[font] if isinstance(font, str) else font
    cells, letters = [], []
    column = line = 0
    for index, char in enumerate(text):
        if char == "\n":
            column, line = 0, line + 1
            continue
        for row, bits in enumerate(f.glyph(char)):
            for x in range(f.width):
                if bits & (1 << (f.width - 1 - x)):
                    cells.append(
                        (column * (f.width + 1) + x, f.height - 1 - row - line * (f.height + 2))
                    )
                    letters.append(index)
        column += 1
    cells = np.array(cells, dtype=np.int64).reshape(-1, 2)
    n = subdivision
    sub = np.stack(np.meshgrid(np.arange(n), np.arange(n)), axis=-1).reshape(-1, 2)
    return (cells[:, None] * n + sub).reshape(-1, 2), np.repeat(np.array(letters, np.int64), n * n)


def wrap_text(text, columns=20):
    """`text` with its lines wrapped at word boundaries to at most `columns` characters
    (existing new lines are kept), ready for text_blocks / create_text_*"""
    return "\n".join(textwrap.fill(line, columns) or "" for line in text.split("\n"))


def text_size(text, font="5x7"):
    """(columns, rows) of grid cells `text` covers (its lines below the first one go down)"""
    f = FONTS[font] if isinstance(font, str) else font
    lines = text.split("\n")
    return max(len(line) for line in lines) * (f.width + 1) - 1, len(lines) * (f.height + 2) - 2


def _colors(colors, n):
    return np.broadcast_to(np.asarray(0 if colors is None else colors, dtype=np.uint32), (n,))


def _block_shape(shape, size):
    """a ball or a square of a block (a small gap: neighbors are not connected)"""
    return b2d.circle(radius=0.45 * size) if shape == "ball" else b2d.box(0.45 * size, 0.45 * size)


def create_blocks(world, cells, origin, size, shape="ball", colors=None, shape_def=None):
    """One dynamic body per block (b2d.Bodies), a "ball" or a "square"; `cells` from
    text_blocks, `size`: the block pitch (m), `colors`: one, or one per block (e.g. by
    letter: `palette[letters]`)"""
    shape_def = shape_def or b2d.shape_def()
    geometry = _block_shape(shape, size)
    bodies = b2d.Bodies()
    for (x, y), color in zip(
        np.asarray(origin) + (cells + 0.5) * size, _colors(colors, len(cells))
    ):
        body = world.create_dynamic_body(position=(float(x), float(y)))
        shape_def.material = b2d.surface_material(custom_color=int(color))
        body.create_shape(shape_def, geometry)
        bodies.append(body)
    return bodies


def create_soft_letters(
    world,
    cells,
    letters,
    origin,
    size,
    shape="ball",
    hertz=5.0,
    damping_ratio=0.3,
    reach=None,
    **kwargs,
):
    """Soft letters: create_blocks (`kwargs`: colors, shape_def) plus a spring (distance
    joint) between every two blocks of the same letter (`reach`: only those at most that
    many blocks apart; None: all pairs, n^2 / 2 joints per letter): (b2d.Bodies, the joints:
    e.g. set their `spring_hertz` to change the stiffness)"""
    bodies = create_blocks(world, cells, origin, size, shape, **kwargs)
    grid = np.rint(cells)  # cells may be jittered: the springs' rest lengths are on the grid
    joints = []
    for letter in np.unique(letters):
        mine = np.flatnonzero(letters == letter)
        a, b = np.triu_indices(len(mine), k=1)
        lengths = np.hypot(*(grid[mine[a]] - grid[mine[b]]).T)
        keep = lengths <= (np.inf if reach is None else reach)
        for i, j, length in zip(mine[a[keep]], mine[b[keep]], lengths[keep]):
            joint = world.create_distance_joint(
                body_a=bodies[int(i)],
                body_b=bodies[int(j)],
                length=size * float(length),
                enable_spring=True,
                hertz=hertz,
                damping_ratio=damping_ratio,
            )
            joints.append(joint)
    return bodies, joints


def create_letters(world, cells, letters, origin, size, colors=None, shape_def=None):
    """One dynamic body per letter, a square per block (b2d.Bodies, rigid letters); `cells`,
    `letters` from text_blocks, `size`: the block pitch (m), `colors`: one, or one per block"""
    shape_def = shape_def or b2d.shape_def()
    centers = np.asarray(origin) + (cells + 0.5) * size
    colors = _colors(colors, len(cells))
    bodies = b2d.Bodies()
    for letter in np.unique(letters):
        mine = np.flatnonzero(letters == letter)
        anchor = centers[mine].mean(axis=0)
        body = world.create_dynamic_body(position=tuple(anchor))
        for k in mine:
            shape_def.material = b2d.surface_material(custom_color=int(colors[k]))
            body.create_shape(
                shape_def, b2d.box(0.5 * size, 0.5 * size, center=tuple(centers[k] - anchor))
            )
        bodies.append(body)
    return bodies

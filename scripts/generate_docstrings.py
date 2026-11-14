"""Generate pyb2d3's docstrings from the doc comments in the box2d headers (``pixi run docstrings``).

box2d documents its API with ``///`` comments. This script turns them into python docstrings,
"applied to pyb2d3": C names become the pyb2d3 names (``b2Body_GetMass`` -> ``Body.mass``,
``b2BodyDef::gravityScale`` -> ``BodyDef.gravity_scale``), ``@param`` / ``@return`` / ``@note``
become ``Args:`` / ``Returns:`` / ``Note:`` sections and the id parameter (the python ``self``)
is dropped.

Outputs (committed, so building does not need this script):

* ``include/pyb2d3/generated/docstrings.hpp``: ``pyb2d3::docs::doc<&b2Fn>`` for every box2d
  function the bindings use. ``Binder`` (ro / rw / def) attaches them automatically, direct
  bindings pass ``docs::doc<&b2Fn>``.
* ``src/module/pyb2d3/_docstrings.py``: docs of the bound structs and their fields, applied to
  the python classes / properties when pyb2d3 is imported.

Usage: python scripts/generate_docstrings.py [--include-dir <box2d include dir>]
(default: $CONDA_PREFIX/include/box2d, i.e. the box2d of the pixi environment)
"""

import argparse
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HEADERS = ["base.h", "math_functions.h", "collision.h", "types.h", "box2d.h"]
OUT_HPP = REPO / "include" / "pyb2d3" / "generated" / "docstrings.hpp"
OUT_PY = REPO / "src" / "module" / "pyb2d3" / "_docstrings.py"

# ---------------------------------------------------------------------------------------------
# reading the box2d headers
# ---------------------------------------------------------------------------------------------

FUNCTION_RE = re.compile(r"^\s*B2_(?:API|INLINE)\b[^;(]*?\b(b2\w+)\s*\(")
STRUCT_BEGIN_RE = re.compile(r"^\s*typedef\s+struct\s+(b2\w+)")
STRUCT_END_RE = re.compile(r"^\s*}\s*(b2\w+)\s*;")
FIELD_RE = re.compile(r"^\s*(?:const\s+)?[\w\s\*]+?[\s\*](\w+)\s*(?:\[[^\]]*\])?\s*;")


def parse_header(text):
    """Doc comments of functions, structs and struct fields."""
    functions, structs, fields = {}, {}, {}
    pending = []
    struct = None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("///"):
            pending.append(stripped[3:].strip())
            continue
        match = FUNCTION_RE.match(line)
        if match and pending:
            functions[match.group(1)] = pending
        match = STRUCT_BEGIN_RE.match(line)
        if match:
            struct = match.group(1)
            if pending:
                structs[struct] = pending
        elif struct is not None:
            if STRUCT_END_RE.match(line):
                struct = None
            else:
                match = FIELD_RE.match(line)
                if match and pending:
                    fields[(struct, match.group(1))] = pending
        if stripped and not stripped.startswith("//"):
            pending = []
        elif not stripped:
            pending = []
    return functions, structs, fields


# ---------------------------------------------------------------------------------------------
# what the bindings use, and under which python names
# ---------------------------------------------------------------------------------------------


def binding_sources():
    files = list((REPO / "src" / "bind").glob("*.cpp")) + list((REPO / "src" / "bind").glob("*.hpp"))
    files += [f for f in (REPO / "include" / "pyb2d3").rglob("*.hpp") if "generated" not in f.parts]
    return "\n".join(f.read_text() for f in files)


def python_names(sources):
    """C function -> python attribute name, C struct -> python class name, (struct, field) -> attr."""
    functions = {}
    # Binder: .ro<b2X>("name") / .rw<b2Get, b2Set>("name") / .def<b2X>("name" (also `template ro<...>`)
    for match in re.finditer(r"\b(?:ro|rw|def)\s*<\s*(&?b2\w+)\s*(?:,\s*(&?b2\w+)\s*)?>\s*\(\s*\"(\w+)\"", sources):
        for c_name in match.group(1, 2):
            if c_name:
                functions.setdefault(c_name.lstrip("&"), match.group(3))
    # direct: def("name", &b2X ...
    for match in re.finditer(r"\bdef\s*\(\s*\"(\w+)\"\s*,\s*&(b2\w+)", sources):
        functions.setdefault(match.group(2), match.group(1))
    classes = {}
    for match in re.finditer(r"<\s*(b2\w+)\b[^<>;]*>\s*\(\s*m\s*,\s*\"(\w+)\"", sources):
        classes.setdefault(match.group(1), match.group(2))
    fields = {}
    for match in re.finditer(r"def_r[wo]\s*\(\s*\"(\w+)\"\s*,\s*&(b2\w+)::(\w+)", sources):
        fields.setdefault((match.group(2), match.group(3)), match.group(1))
    return functions, classes, fields


def used_functions(sources):
    return set(re.findall(r"\b(b2[A-Z]\w*)\b", sources))


# ---------------------------------------------------------------------------------------------
# turning box2d's text into pyb2d3 docstrings
# ---------------------------------------------------------------------------------------------


def snake(name):
    return re.sub(r"(?<=[a-z0-9])([A-Z])", r"_\1", name).lower()


def owner_class(c_function):
    """b2Body_GetMass -> 'Body', b2MakeRot -> None (module function)."""
    match = re.match(r"b2(\w+?)_\w+", c_function)
    return match.group(1) if match else None


class Renderer:
    def __init__(self, functions, classes, fields):
        self.functions, self.classes, self.fields = functions, classes, fields

    def class_name(self, c_struct):
        return self.classes.get(c_struct, c_struct[2:] if c_struct.startswith("b2") else c_struct)

    def function_ref(self, c_function):
        name = self.functions.get(c_function)
        if name is None:
            return None
        owner = owner_class(c_function)
        return f"{owner}.{name}" if owner else name

    def references(self, text):
        """C identifiers in prose -> pyb2d3 names."""

        def field(match):
            struct, member = match.group(1), match.group(2)
            attr = self.fields.get((struct, member), snake(member))
            return f"``{self.class_name(struct)}.{attr}``"

        def function(match):
            ref = self.function_ref(match.group(1))
            return f"``{ref}``" if ref else f"``{match.group(1)}``"

        # python defs are created with their defaults (BodyDef() / body_def())
        text = re.sub(r"\s*Must be initialized using \S+\.?", "", text)
        text = re.sub(r"\bb2Default(\w+?)\s*(?:\(\s*\))?(?=[\s.,;:)]|$)", lambda m: f"``{snake(m.group(1))}()``", text)
        text = re.sub(r"\b(b2\w+)::(\w+)", field, text)
        text = re.sub(r"\b(b2[A-Z]\w*_\w+|b2[A-Z][a-z]\w*)\s*\(\s*\)", function, text)
        text = re.sub(r"\b(b2[A-Z]\w*_[A-Z]\w*)\b", function, text)

        def type_or_function(match):
            name = match.group(1)
            ref = self.function_ref(name)
            if ref:
                return f"``{ref}``"
            return f"``{self.class_name(name)}``"

        text = re.sub(r"(?<!`)\b(b2[A-Z]\w*)\b(?!`)", type_or_function, text)
        text = re.sub(r"\b(\d+\.\d*)f\b", r"\1", text)  # 1.0f -> 1.0
        # rst: an inline literal must not be directly followed by "(" or a letter (as in a
        # call `inv_mul_transforms( a, b )`), an escaped space joins them invisibly
        text = re.sub(r"(``[^`]+``)(?=[(\w])", r"\1\\ ", text)
        return text

    def render(self, lines, drop_param=None, as_property=False):
        """box2d doc lines -> docstring."""
        summary, params, sections = [], [], []
        current = summary
        for line in lines:
            match = re.match(r"@(\w+)\s*(.*)", line)
            if not match:
                current.append(line)
                continue
            tag, rest = match.groups()
            if tag == "param":
                name, _, desc = rest.partition(" ")
                current = [snake(name), desc.strip()]
                if name != drop_param:
                    params.append(current)
            elif tag in ("return", "returns"):
                current = ["Returns:", rest]
                sections.append(current)
            elif tag in ("note", "warning", "see"):
                title = {"note": "Note:", "warning": "Warning:", "see": "See also:"}[tag]
                current = [title, rest]
                sections.append(current)
            else:  # @ingroup, @defgroup, @{ ...
                current = []
        text = " ".join(part for part in summary if part).strip()
        if as_property:
            text = re.sub(r"^(?:Get|Gets)\s+(?:the\s+)?(\w)", lambda m: m.group(1).upper(), text)
            text = re.sub(r"^Returns\s+(?:the\s+)?(\w)", lambda m: m.group(1).upper(), text)
        out = [self.references(text)]
        if params:
            out.append("Args:\n" + "\n".join(f"    {p[0]}: {self.references(' '.join(p[1:]).strip())}" for p in params))
        for section in sections:
            out.append(f"{section[0]}\n    {self.references(' '.join(section[1:]).strip())}")
        return "\n\n".join(part for part in out if part.strip())


# ---------------------------------------------------------------------------------------------
# output
# ---------------------------------------------------------------------------------------------

HPP_HEADER = """\
// generated by scripts/generate_docstrings.py from the box2d headers, do not edit
// (regenerate with `pixi run docstrings`)
#pragma once

#include <box2d/box2d.h>
#include <box2d/collision.h>
#include <box2d/math_functions.h>

namespace pyb2d3::docs
{{
    // docstring of a box2d function, "" if box2d has none
    template <auto F>
    inline constexpr const char* doc = "";

{entries}
}}  // namespace pyb2d3::docs
"""


def cpp_string(text):
    return f'R"pyb2d3doc({text})pyb2d3doc"'


def default_include_dir():
    if os.environ.get("CONDA_PREFIX"):
        include_dir = Path(os.environ["CONDA_PREFIX"]) / "include" / "box2d"
        if (include_dir / "box2d.h").exists():
            return include_dir
    return None


def generate(include_dir):
    """The contents of the generated files ({path: text}) and a summary line."""
    functions, structs, fields = {}, {}, {}
    texts = {header: (include_dir / header).read_text() for header in HEADERS}
    for text in texts.values():
        f, s, fl = parse_header(text)
        functions.update(f)
        structs.update(s)
        fields.update(fl)
    all_headers = "\n".join(texts.values())

    sources = binding_sources()
    used = used_functions(sources)
    py_functions, py_classes, py_fields = python_names(sources)
    renderer = Renderer(py_functions, py_classes, py_fields)

    entries = []
    for name in sorted(used & set(functions)):
        lines = functions[name]
        drop = None
        if owner_class(name):
            # the id parameter is `self` in python
            match = re.search(rf"\b{name}\s*\(\s*\w+\s+(\w+Id)\b", all_headers)
            drop = match.group(1) if match else None
        is_getter = re.match(r"b2\w+_(?:Get|Is|Has)", name) is not None
        doc = renderer.render(lines, drop_param=drop, as_property=is_getter)
        entries.append(f"    template <>\n    inline constexpr const char* doc<&{name}> = {cpp_string(doc)};\n")

    class_docs = {}
    for struct, lines in structs.items():
        if struct in py_classes:
            class_docs[py_classes[struct]] = renderer.render(lines)
    field_docs = {}
    for (struct, member), attr in py_fields.items():
        if (struct, member) in fields and struct in py_classes:
            field_docs[(py_classes[struct], attr)] = renderer.render(fields[(struct, member)])

    py = ['"""Generated by scripts/generate_docstrings.py from the box2d headers, do not edit."""', ""]
    py.append("CLASS_DOCS = {")
    py += [f"    {name!r}: {class_docs[name]!r}," for name in sorted(class_docs)]
    py += ["}", "", "FIELD_DOCS = {"]
    py += [f"    {key!r}: {field_docs[key]!r}," for key in sorted(field_docs)]
    py.append("}")

    summary = (
        f"{len(entries)} function docs -> {OUT_HPP.relative_to(REPO)}, "
        f"{len(class_docs)} class and {len(field_docs)} field docs -> {OUT_PY.relative_to(REPO)}"
    )
    return {OUT_HPP: HPP_HEADER.format(entries="\n".join(entries)), OUT_PY: "\n".join(py) + "\n"}, summary


def stale_files(include_dir):
    """Generated files that differ from what the current headers / bindings produce."""
    outputs, _ = generate(include_dir)
    return [path for path, text in outputs.items() if not path.exists() or path.read_text() != text]


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--include-dir", type=Path)
    parser.add_argument("--check", action="store_true", help="only check that the generated files are current")
    args = parser.parse_args()
    include_dir = args.include_dir or default_include_dir()
    if include_dir is None or not (include_dir / "box2d.h").exists():
        sys.exit("box2d headers not found, pass --include-dir")

    if args.check:
        stale = stale_files(include_dir)
        if stale:
            sys.exit("out of date (run `pixi run docstrings`): " + ", ".join(str(p.relative_to(REPO)) for p in stale))
        print("generated docstrings are up to date")
        return

    outputs, summary = generate(include_dir)
    for path, text in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    print(summary)


if __name__ == "__main__":
    main()

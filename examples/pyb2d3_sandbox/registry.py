"""Grouping of samples into categories, like box2d's own sample browser.

Register a sample with the decorator::

    @register_sample("Joints", "Revolute")
    class Revolute(SampleBase):
        ...

Frontends use the registry to show a categorized sample browser and to
switch between samples.
"""

from dataclasses import dataclass


def _same_class(a, b):
    """the same class, or a new version of it (its module re-imported after
    editing the code: same module and qualified name)"""
    return a is b or (a.__module__ == b.__module__ and a.__qualname__ == b.__qualname__)


@dataclass(frozen=True)
class SampleEntry:
    category: str
    name: str
    cls: type
    video: bool = False  # worth a video in the docs' sample gallery

    @property
    def key(self):
        return f"{self.category}/{self.name}"


class SampleRegistry(object):
    def __init__(self):
        # category -> name -> entry, both in registration order
        self._categories = {}

    def register(self, cls, category, name=None, video=False):
        name = name or cls.__name__
        entries = self._categories.setdefault(category, {})
        if name in entries and not _same_class(entries[name].cls, cls):
            raise ValueError(f"a different sample is already registered as '{category}/{name}'")
        entries[name] = SampleEntry(category, name, cls, video)
        cls.sample_category = category
        cls.sample_name = name
        return cls

    def categories(self):
        return list(self._categories)

    def samples(self, category=None):
        if category is not None:
            return list(self._categories.get(category, {}).values())
        return [entry for entries in self._categories.values() for entry in entries.values()]

    def __iter__(self):
        return iter(self.samples())

    def __len__(self):
        return sum(len(entries) for entries in self._categories.values())

    def __contains__(self, cls):
        return any(entry.cls is cls for entry in self)

    def get(self, key):
        """Entry for 'Category/Name'."""
        category, _, name = key.partition("/")
        try:
            return self._categories[category][name]
        except KeyError:
            raise KeyError(f"no sample registered as '{key}'") from None

    def find(self, cls):
        """Entry of a sample class, or None if it is not registered."""
        for entry in self:
            if entry.cls is cls:
                return entry
        return None

    def replace_classes(self, modules):
        """Point the entries of samples defined in `modules` to the classes of the
        same name in them (after the modules were re-imported). Returns {old: new}."""
        by_name = {module.__name__: module for module in modules}
        replaced = {}
        for entries in self._categories.values():
            for name, entry in entries.items():
                module = by_name.get(entry.cls.__module__)
                new = getattr(module, entry.cls.__qualname__, None) if module else None
                if isinstance(new, type) and new is not entry.cls:
                    replaced[entry.cls] = new
                    entries[name] = SampleEntry(entry.category, entry.name, new, entry.video)
                    new.sample_category, new.sample_name = entry.category, entry.name
        return replaced

    def neighbor(self, cls, step=1):
        """The entry `step` places after (or before) `cls`, wrapping around."""
        entries = self.samples()
        if not entries:
            return None
        current = self.find(cls)
        index = entries.index(current) if current is not None else -step if step > 0 else 0
        return entries[(index + step) % len(entries)]


registry = SampleRegistry()


def register_sample(category, name=None, video=False, registry=registry):
    """Class decorator: register a sample under `category` / `name` (default: class name).
    `video=True`: the docs show it in the sample gallery (a video rendered headless)."""

    def decorator(cls):
        return registry.register(cls, category, name, video)

    return decorator

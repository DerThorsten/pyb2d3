"""Grouping of samples into categories, like box2d's own sample browser.

Register a sample with the decorator::

    @register_sample("Joints", "Revolute")
    class Revolute(SampleBase):
        ...

Frontends use the registry to show a categorized sample browser and to
switch between samples.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SampleEntry:
    category: str
    name: str
    cls: type

    @property
    def key(self):
        return f"{self.category}/{self.name}"


class SampleRegistry(object):
    def __init__(self):
        # category -> name -> entry, both in registration order
        self._categories = {}

    def register(self, cls, category, name=None):
        name = name or cls.__name__
        entries = self._categories.setdefault(category, {})
        if name in entries and entries[name].cls is not cls:
            raise ValueError(f"a different sample is already registered as '{category}/{name}'")
        entries[name] = SampleEntry(category, name, cls)
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

    def neighbor(self, cls, step=1):
        """The entry `step` places after (or before) `cls`, wrapping around."""
        entries = self.samples()
        if not entries:
            return None
        current = self.find(cls)
        index = entries.index(current) if current is not None else -step if step > 0 else 0
        return entries[(index + step) % len(entries)]


registry = SampleRegistry()


def register_sample(category, name=None, registry=registry):
    """Class decorator: register a sample under `category` / `name` (default: class name)."""

    def decorator(cls):
        return registry.register(cls, category, name)

    return decorator

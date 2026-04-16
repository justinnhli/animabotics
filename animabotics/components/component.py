"""The base class for all components."""

from typing import Any

class Component:
    """The base class for all components."""

    @property
    def components(self):
        # type: () -> tuple[type, ...]
        """List all components."""
        return tuple(
            cls for cls in type(self).mro()
            if issubclass(cls, Component)
        )

    def _clear_cached_property(self, property_name):
        # type: (str) -> None
        """Clear the cached value of a specific property."""
        self.__dict__.pop(property_name, None)

    def _clear_cache(self, **kwargs):
        # type: (**Any) -> None
        """Clear the cache of data used by this class."""
        # pylint: disable = unused-argument
        pass

    def clear_cache(self, root_cls, **kwargs):
        # type: (type, **Any) -> None
        """Clear the cache up to the root class."""
        # pylint: disable = protected-access
        assert issubclass(root_cls, Component)
        for cls in type(self).mro():
            if issubclass(cls, root_cls):
                cls._clear_cache(self, **kwargs)


class NeedsUpdates(Component):
    """Components that need to be updated every tick."""

    def update(self, elapsed_msec, elapsed_msec_squared):
        # type: (int, int) -> None
        """Update the component."""
        raise NotImplementedError()

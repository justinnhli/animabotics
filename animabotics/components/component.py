"""The base class for all components."""

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

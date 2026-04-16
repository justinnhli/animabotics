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


class NeedsUpdates(Component):
    """Components that need to be updated every tick."""

    def update(self, elapsed_msec, elapsed_msec_squared):
        # type: (int, int) -> None
        """Update the component."""
        raise NotImplementedError()

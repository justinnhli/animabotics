"""Tests for game.py."""

from animabotics import Game, get_msec


class DummyGame(Game):
    """A dummy game to test callbacks and Game.stop()."""

    def __init__(self):
        # type: () -> None
        super().__init__(180, 120)


def test_game_stop():
    # type: () -> None
    """Test callbacks and Game.stop()."""
    game = DummyGame()
    start_time = get_msec()
    game.start((250, game.stop))
    elapsed_time = get_msec() - start_time
    assert elapsed_time < 300

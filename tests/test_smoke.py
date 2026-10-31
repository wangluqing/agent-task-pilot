"""Project scaffold smoke tests."""

from agent_task_pilot import __version__


def test_package_is_importable() -> None:
    """The src-layout package can be imported after project installation."""
    assert __version__ == "0.1.0"

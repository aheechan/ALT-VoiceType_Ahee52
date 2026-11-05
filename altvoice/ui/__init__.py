"""Qt UI package (optional, imported only by the ``run`` command)."""


def run_tray(config_path: str | None = None) -> int:
    from .tray import run_tray as _run_tray

    return _run_tray(config_path)


__all__ = ["run_tray"]

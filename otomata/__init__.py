"""Otomata - CLI tools for automation."""

__version__ = "0.3.0"


def _check_update():
    """Non-blocking check for newer version on GitHub."""
    import os

    if os.environ.get("OTOMATA_NO_UPDATE_CHECK"):
        return

    import threading

    def _check():
        try:
            import json
            import urllib.request

            url = "https://api.github.com/repos/AlexisLaporte/otomata-tools/releases/latest"
            req = urllib.request.Request(url, headers={"Accept": "application/vnd.github.v3+json"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                latest = json.loads(resp.read()).get("tag_name", "").lstrip("v")
                if latest and latest != __version__:
                    import warnings

                    warnings.warn(
                        f"otomata {latest} disponible (installé: {__version__}). "
                        f"Upgrade: pip install -U git+https://github.com/AlexisLaporte/otomata-tools.git",
                        stacklevel=2,
                    )
        except Exception:
            pass

    threading.Thread(target=_check, daemon=True).start()


_check_update()

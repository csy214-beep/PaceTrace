import logging
import os

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
_INITIALIZED = False


def init_logging():
    global _INITIALIZED
    if _INITIALIZED:
        return
    _INITIALIZED = True

    os.makedirs(LOG_DIR, exist_ok=True)
    path = os.path.join(LOG_DIR, "app.log")

    # Truncate file on first run only
    if os.path.exists(path):
        try:
            with open(path, "w") as f:
                f.write("")
        except Exception:
            pass

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-5s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    def make(name):
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        if not logger.handlers:
            fh = logging.FileHandler(path, encoding="utf-8")
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(fmt)
            logger.addHandler(fh)
        return logger

    ui_logger = make("app")

    import api.client as api_client
    api_client._logger = make("api")

    return ui_logger


logger = init_logging()

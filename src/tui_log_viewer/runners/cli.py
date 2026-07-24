import logging

logger = logging.getLogger(__name__)


def main():
    try:
        print(f"Hello from {__file__}")

    except Exception:
        logger.exception("Unhandled exception in CLI.")


if __name__ == "__main__":
    print("This module should not be imported")
    raise ImportError("logtui.runners.cli is not importable")

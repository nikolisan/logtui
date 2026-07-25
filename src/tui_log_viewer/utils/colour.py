from __future__ import annotations

import logging
from enum import Enum
from typing import Any


class ColourEnum(Enum):
    RED = "31"
    GREEN = "32"
    YELLOW = "33"
    BLUE = "34"
    MAGENTA = "35"
    CYAN = "36"
    WHITE = "37"


class ColouredMeta(type):
    def __new__(
        mcs, name: str, bases: tuple[type, ...], namespace: dict[str, Any]
    ) -> type:
        def _method_factory(method_name: str, code: str) -> Any:
            @classmethod
            def method(
                cls: type[Coloured],
                text: str,
                bold: bool = False,
                reverse: bool = False,
            ) -> Any:
                return cls.format(text, code, bold, reverse)

            method.__name__ = method_name
            method.__qualname__ = f"{name}.{method_name}"
            return method

        for colour in ColourEnum:
            namespace[colour.name] = _method_factory(colour.name, colour.value)

        return super().__new__(mcs, name, bases, namespace)


class Coloured(metaclass=ColouredMeta):
    RESET = "\033[0m"

    def __init__(self, colour_code: str) -> None:
        self.colour_code = colour_code

    def __call__(self, text: str) -> str:
        return f"\033[{self.colour_code}m{text}{self.RESET}"

    @classmethod
    def format(
        cls, text: str, code: str, bold: bool = False, reverse: bool = False
    ) -> str:
        codes: list[str] = []
        if bold:
            codes.append("1")
        if reverse:
            codes.append("7")
        codes.append(code)
        return cls(";".join(codes))(text)

    @classmethod
    def for_level(
        cls, text: str, level: str | int, *, bold: bool = False, reverse: bool = False
    ) -> str:
        if isinstance(level, str):
            level_number = logging.getLevelNamesMapping().get(level.upper())
            if level_number is None:
                raise ValueError(f"Invalid log level: {level!r}")
            level = level_number

        if level >= logging.CRITICAL:
            colour = ColourEnum.MAGENTA
        elif level >= logging.ERROR:
            colour = ColourEnum.RED
        elif level >= logging.WARNING:
            colour = ColourEnum.YELLOW
        elif level >= logging.INFO:
            colour = ColourEnum.GREEN
        else:
            colour = ColourEnum.CYAN

        return cls.format(text, colour.value, bold, reverse)

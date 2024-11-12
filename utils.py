try:
    import colored
except ImportError:
    colored = None

class color:
    if colored:
        def green(text: str) -> str:
            return colored.stylize(text, colored.fg("green"))

        def red(text: str) -> str:
            return colored.stylize(text, colored.fg("red"))

        def yellow(text: str) -> str:
            return colored.stylize(text, colored.fg("yellow"))

        def blue(text: str) -> str:
            return colored.stylize(text, colored.fg("blue"))

        def magenta(text: str) -> str:
            return colored.stylize(text, colored.fg("magenta"))

        def cyan(text: str) -> str:
            return colored.stylize(text, colored.fg("cyan"))

        def white(text: str) -> str:
            return colored.stylize(text, colored.fg("white"))

        def bold(text: str) -> str:
            return colored.stylize(text, colored.attr("bold"))
    else:
        def _missing(text: str) -> str:
            return text

        green = red = yellow = blue = magenta = cyan = white = bold = _missing

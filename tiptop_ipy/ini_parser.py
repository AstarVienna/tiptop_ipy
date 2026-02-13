"""
Reliable INI parser for TIPTOP-style .ini files.

TIPTOP .ini files are non-standard: they use Python list literals,
scientific notation, None values, both ';' and '#' comments, and
sometimes have '=' inside string values.
"""
import ast
import re


def parse_ini(path_or_string):
    """Parse a TIPTOP .ini file into nested dict {section: {key: value}}.

    Parameters
    ----------
    path_or_string : str or Path
        Either a file path or the raw INI string contents.

    Returns
    -------
    config : dict[str, dict[str, Any]]
        Nested dictionary of {section: {key: value}}.
    """
    # Determine if it's a file path or raw string
    text = path_or_string
    if "\n" not in str(path_or_string) and "[" not in str(path_or_string):
        try:
            with open(path_or_string, "r") as f:
                text = f.read()
        except (OSError, FileNotFoundError):
            pass  # treat as raw string

    config = {}
    current_section = None

    for line in str(text).splitlines():
        # Strip comments: both ; and # (but not inside quotes)
        stripped = _strip_comments(line).strip()

        if not stripped:
            continue

        # Section header
        match = re.match(r"^\[(.+)\]$", stripped)
        if match:
            current_section = match.group(1).strip()
            config[current_section] = {}
            continue

        # Key = value
        if current_section is not None and "=" in stripped:
            key, _, raw_value = stripped.partition("=")
            key = key.strip()
            raw_value = raw_value.strip()

            if key and raw_value:
                config[current_section][key] = _parse_value(raw_value)
            elif key:
                config[current_section][key] = ""

    return config


def write_ini(config, path=None):
    """Write config dict to .ini format string (and optionally to file).

    Parameters
    ----------
    config : dict[str, dict[str, Any]]
        Nested dictionary of {section: {key: value}}.
    path : str or Path, optional
        If provided, write to this file path.

    Returns
    -------
    ini_string : str
        The formatted INI string.
    """
    lines = []
    for section, params in config.items():
        lines.append(f"[{section}]")
        for key, value in params.items():
            lines.append(f"{key} = {_format_value(value)}")
        lines.append("")

    ini_string = "\n".join(lines)

    if path is not None:
        with open(path, "w") as f:
            f.write(ini_string)

    return ini_string


def _strip_comments(line):
    """Remove ; and # comments from a line, respecting quoted strings."""
    in_single = False
    in_double = False
    in_bracket = 0

    for i, ch in enumerate(line):
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == "[":
            in_bracket += 1
        elif ch == "]":
            in_bracket = max(0, in_bracket - 1)
        elif ch in (";", "#") and not in_single and not in_double and in_bracket == 0:
            return line[:i]

    return line


def _parse_value(raw):
    """Parse a single INI value string into a Python object.

    Uses ast.literal_eval where possible, with fallbacks for
    TIPTOP-specific formats (None, scientific notation, etc.).
    """
    # Handle quoted strings - strip outer quotes and return as string
    if (raw.startswith("'") and raw.endswith("'")) or \
       (raw.startswith('"') and raw.endswith('"')):
        return raw[1:-1]

    # Try ast.literal_eval first (handles lists, tuples, numbers, True/False/None)
    try:
        return ast.literal_eval(raw)
    except (ValueError, SyntaxError):
        pass

    # Handle bare None
    if raw == "None":
        return None

    # Handle bare True/False
    if raw == "True":
        return True
    if raw == "False":
        return False

    # Handle scientific notation without decimal point (e.g., 500e-9, 589e-9)
    # ast.literal_eval doesn't handle these
    try:
        if re.match(r"^[+-]?\d+[eE][+-]?\d+$", raw):
            return float(raw)
    except ValueError:
        pass

    # Handle lists containing scientific notation that ast couldn't parse
    if raw.startswith("[") and raw.endswith("]"):
        return _parse_list(raw)

    # Fallback: return as string
    return raw


def _parse_list(raw):
    """Parse a list string that may contain scientific notation values."""
    inner = raw[1:-1].strip()
    if not inner:
        return []

    elements = []
    # Split respecting nested brackets
    depth = 0
    current = ""
    for ch in inner:
        if ch == "[":
            depth += 1
            current += ch
        elif ch == "]":
            depth -= 1
            current += ch
        elif ch == "," and depth == 0:
            elements.append(current.strip())
            current = ""
        else:
            current += ch
    if current.strip():
        elements.append(current.strip())

    return [_parse_value(e) for e in elements]


def _format_value(value):
    """Format a Python value for INI output."""
    if value is None:
        return "None"
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, str):
        return f"'{value}'"
    if isinstance(value, list):
        return _format_list(value)
    if isinstance(value, float):
        # Use repr to preserve precision, but clean up
        return repr(value)
    return str(value)


def _format_list(lst):
    """Format a list for INI output."""
    if not lst:
        return "[]"
    formatted = [_format_value(item) for item in lst]
    return f"[{', '.join(formatted)}]"

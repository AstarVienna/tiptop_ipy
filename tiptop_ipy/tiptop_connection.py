"""Main interface to the TIPTOP PSF simulation microservice."""
from copy import deepcopy
import os
import os.path as p

from . import utils
from .ini_parser import parse_ini, write_ini
from .result import TipTopResult
from .validation import validate_config


class TipTop:
    """Main interface to the TIPTOP microservice.

    Usage::

        tt = TipTop("MICADO_SCAO")           # Load from template
        tt["atmosphere", "Seeing"] = 0.6      # Tweak parameters
        tt["telescope", "ZenithAngle"] = 15.0
        result = tt.generate_psf()            # Run simulation
        result.plot()                         # View PSF

    Parameters
    ----------
    instrument : str, optional
        Template name (e.g. "MICADO_SCAO", "ERIS", "MORFEO").
        Matched case-insensitively against available templates.
    ini_file : str, optional
        Path to a custom .ini file.

    Either instrument or ini_file must be provided.
    If neither is given, defaults are used.
    """

    def __init__(self, instrument=None, ini_file=None):
        self._instrument = None
        self._config = None
        self._original_config = None

        if instrument is not None:
            self._instrument = instrument
            path = self._resolve_template(instrument)
            self._config = parse_ini(path)
            self._original_config = deepcopy(self._config)

        elif ini_file is not None:
            self._config = parse_ini(ini_file)
            self._original_config = deepcopy(self._config)

        else:
            # Use bare defaults (strip description/required_keywords)
            self._config = self._clean_defaults()
            self._original_config = deepcopy(self._config)

    @staticmethod
    def _resolve_template(instrument):
        """Find the template .ini file for a given instrument name."""
        templates_dir = p.join(p.dirname(__file__), "instrument_templates")

        # Try exact match first
        exact = p.join(templates_dir, f"{instrument}.ini")
        if os.path.exists(exact):
            return exact

        # Try with .ini extension already included
        if instrument.endswith(".ini"):
            exact = p.join(templates_dir, instrument)
            if os.path.exists(exact):
                return exact

        # Case-insensitive search
        instrument_lower = instrument.lower().replace(".ini", "")
        for fname in os.listdir(templates_dir):
            if fname.lower().replace(".ini", "") == instrument_lower and fname.endswith(".ini"):
                return p.join(templates_dir, fname)

        available = ", ".join(TipTop.list_instruments())
        raise FileNotFoundError(
            f"No template found for '{instrument}'. "
            f"Available: {available}"
        )

    @staticmethod
    def _clean_defaults():
        """Return defaults with description/required_keywords stripped."""
        config = {}
        for section, params in utils.DEFAULTS_YAML.items():
            if not isinstance(params, dict):
                continue
            config[section] = {
                k: deepcopy(v) for k, v in params.items()
                if k not in ("description", "required_keywords")
            }
        return config

    # --- Parameter access via tuple indexing ---

    def __getitem__(self, key):
        """Access config values.

        tt["atmosphere"] returns the whole section dict.
        tt["atmosphere", "Seeing"] returns a single value.
        """
        if isinstance(key, tuple):
            section, param = key
            return self._config[section][param]
        return self._config[key]

    def __setitem__(self, key, value):
        """Set config values.

        tt["atmosphere", "Seeing"] = 0.6
        tt["atmosphere"] = {"Seeing": 0.6, ...}  # replace whole section
        """
        if isinstance(key, tuple):
            section, param = key
            if section not in self._config:
                self._config[section] = {}
            self._config[section][param] = value
        else:
            self._config[key] = value

    # --- Core methods ---

    def generate_psf(self, timeout=120):
        """Send config to TIPTOP server and return a TipTopResult.

        Validates config before sending and shows progress feedback.

        Parameters
        ----------
        timeout : int
            Request timeout in seconds.

        Returns
        -------
        result : TipTopResult
            The simulation result with PSF data.
        """
        issues = self.validate()
        errors = [i for i in issues if i.startswith("ERROR")]
        if errors:
            raise ValueError(
                "Config has errors:\n" + "\n".join(errors)
            )

        ini_string = write_ini(self._config)
        hdulist = utils.query_tiptop_server(ini_string, timeout=timeout)
        return TipTopResult(hdulist)

    def validate(self):
        """Check config for errors/warnings without sending.

        Returns
        -------
        issues : list[str]
            List of error/warning strings. Empty = valid.
        """
        return validate_config(self._config)

    def save(self, path):
        """Save current config as .ini file.

        Parameters
        ----------
        path : str
            Output file path.
        """
        write_ini(self._config, path)

    def load(self, path):
        """Load config from .ini file, replacing current config.

        Parameters
        ----------
        path : str
            Path to .ini file.
        """
        self._config = parse_ini(path)
        self._original_config = deepcopy(self._config)

    def reset(self):
        """Reset to original template values."""
        self._config = deepcopy(self._original_config)

    def diff(self):
        """Show what changed from the template.

        Returns
        -------
        changes : dict
            Nested dict of {section: {key: (old, new)}} for changed values.
        """
        changes = {}
        for section in self._config:
            if section not in self._original_config:
                changes[section] = {
                    k: (None, v) for k, v in self._config[section].items()
                }
                continue
            for key, new_val in self._config[section].items():
                old_val = self._original_config.get(section, {}).get(key)
                if old_val != new_val:
                    changes.setdefault(section, {})[key] = (old_val, new_val)

        # Check for removed keys
        for section in self._original_config:
            if section not in self._config:
                changes[section] = {
                    k: (v, None)
                    for k, v in self._original_config[section].items()
                }
                continue
            for key, old_val in self._original_config[section].items():
                if key not in self._config.get(section, {}):
                    changes.setdefault(section, {})[key] = (old_val, None)

        return changes

    @property
    def sections(self):
        """List of config section names."""
        return list(self._config.keys())

    @property
    def ini_contents(self):
        """The INI string representation of the current config."""
        return write_ini(self._config)

    # --- Display ---

    def _repr_html_(self):
        """Jupyter: HTML table of all sections/params with changed values highlighted."""
        changes = self.diff()
        rows = []
        for section in self._config:
            for key, value in self._config[section].items():
                changed = section in changes and key in changes[section]
                style = ' style="background-color: #ffffcc;"' if changed else ""
                rows.append(
                    f"<tr{style}><td><b>{section}</b></td>"
                    f"<td>{key}</td><td>{_format_html_value(value)}</td></tr>"
                )

        name = self._instrument or "custom"
        n_changes = sum(len(v) for v in changes.values())
        header = f"<b>TipTop</b>: {name}"
        if n_changes:
            header += f" ({n_changes} change{'s' if n_changes != 1 else ''})"

        table = (
            "<table>"
            "<tr><th>Section</th><th>Parameter</th><th>Value</th></tr>"
            + "".join(rows) +
            "</table>"
        )
        return f"{header}<br>{table}"

    def __repr__(self):
        name = self._instrument or "custom"
        n_sections = len(self._config)
        n_params = sum(len(v) for v in self._config.values())
        changes = self.diff()
        n_changes = sum(len(v) for v in changes.values())
        parts = [f"TipTop('{name}', {n_sections} sections, {n_params} params"]
        if n_changes:
            parts[0] += f", {n_changes} changed"
        parts[0] += ")"
        return parts[0]

    # --- Class methods ---

    @classmethod
    def list_instruments(cls):
        """List available instrument templates.

        Returns
        -------
        names : list[str]
            Sorted list of instrument template names.
        """
        return utils.list_instruments()

    @staticmethod
    def ping():
        """Check if the TIPTOP server is reachable.

        Returns
        -------
        reachable : bool
        """
        import requests
        try:
            r = requests.get(
                "https://www.eso.org/p2services/any/tiptop",
                timeout=10,
            )
            return r.status_code < 500
        except requests.RequestException:
            return False


# Keep backward compatibility
TipTopConnection = TipTop


def _format_html_value(value):
    """Format a value for HTML display, truncating long lists."""
    s = repr(value)
    if len(s) > 80:
        s = s[:77] + "..."
    return s

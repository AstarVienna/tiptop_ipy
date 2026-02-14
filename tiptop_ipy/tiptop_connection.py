"""Main interface to the TIPTOP PSF simulation microservice."""
from copy import deepcopy
import math
import os
import os.path as p

import numpy as np
import astropy.units as u

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

    MAX_FOV = 512
    """Hard limit on ``sensor_science.FieldOfView`` when loading INI files.

    Templates and user INI files may specify very large fields of view
    (e.g. 2048 for MICADO) that cause the ESO server to time out.  Values
    above this cap are silently reduced on load.  Users can still increase
    the value afterwards via ``tt["sensor_science", "FieldOfView"] = N``.
    """

    def __init__(self, instrument=None, ini_file=None):
        self._instrument = None
        self._config = None
        self._original_config = None

        if instrument is not None:
            self._instrument = instrument
            path = self._resolve_template(instrument)
            self._config = parse_ini(path)
            self._cap_fov()
            self._original_config = deepcopy(self._config)

        elif ini_file is not None:
            self._config = parse_ini(ini_file)
            self._cap_fov()
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

    def _cap_fov(self):
        """Cap sensor_science.FieldOfView to MAX_FOV on load."""
        sec = self._config.get("sensor_science")
        if sec and isinstance(sec.get("FieldOfView"), (int, float)):
            if sec["FieldOfView"] > self.MAX_FOV:
                sec["FieldOfView"] = self.MAX_FOV

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
        self._cap_fov()
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

    # --- Wavelengths ---

    @property
    def wavelengths(self):
        """Science wavelengths as an astropy Quantity in microns.

        Reads ``sources_science.Wavelength`` (stored in metres internally)
        and returns values as ``u.um``.

        Returns
        -------
        wavelengths : astropy.units.Quantity
            Wavelengths in microns.
        """
        wl = self._config.get("sources_science", {}).get("Wavelength", [])
        if not isinstance(wl, list):
            wl = [wl]
        return (np.asarray(wl, dtype=float) * u.m).to(u.um)

    @wavelengths.setter
    def wavelengths(self, values):
        """Set science wavelengths.

        Parameters
        ----------
        values : Quantity, float, or list
            Wavelength(s). If an astropy Quantity, converted to metres.
            If plain floats, assumed to be in microns.
        """
        if isinstance(values, u.Quantity):
            metres = values.to(u.m).value
        else:
            if isinstance(values, (int, float)):
                values = [values]
            metres = [v * 1e-6 for v in values]
        if not hasattr(metres, '__len__'):
            metres = [metres]
        else:
            metres = list(metres)
        self["sources_science", "Wavelength"] = metres

    # --- Positions ---

    @property
    def positions(self):
        """Science source positions as (x, y) Quantities in arcsec.

        Computed from ``sources_science.Zenith`` (radial distance) and
        ``sources_science.Azimuth`` (angle in degrees).

        Returns
        -------
        x, y : astropy.units.Quantity
            Cartesian coordinates in arcsec.
        """
        zenith = self._config.get("sources_science", {}).get("Zenith", [0.0])
        azimuth = self._config.get("sources_science", {}).get("Azimuth", [0.0])
        zenith = np.asarray(zenith, dtype=float)
        azimuth_rad = np.deg2rad(azimuth)
        x = zenith * np.cos(azimuth_rad)
        y = zenith * np.sin(azimuth_rad)
        return x * u.arcsec, y * u.arcsec

    def add_off_axis_positions(self, positions):
        """Set science source positions from (x, y) coordinates.

        Converts Cartesian (x, y) to polar (Zenith, Azimuth) and updates
        ``sources_science.Zenith`` and ``sources_science.Azimuth``.

        Parameters
        ----------
        positions : tuple or list of tuples
            A single ``(x, y)`` tuple or a list of ``(x, y)`` tuples.
            If values are astropy Quantities, they are converted to arcsec.
            If plain floats, assumed to be in arcsec.

        Examples
        --------
        ::

            tt = TipTop("ERIS")
            tt.add_off_axis_positions((0, 0))           # on-axis only
            tt.add_off_axis_positions([(0, 0), (5, 5)])  # on-axis + 5",5"

            # With units
            import astropy.units as u
            tt.add_off_axis_positions([(0, 0)*u.arcsec, (5, 5)*u.arcsec])
        """
        # Accept a single (x, y) tuple
        if (isinstance(positions, tuple)
                and len(positions) == 2
                and not isinstance(positions[0], (list, tuple))):
            positions = [positions]

        zeniths = []
        azimuths = []
        for x, y in positions:
            # Convert Quantities to arcsec
            if isinstance(x, u.Quantity):
                x = x.to(u.arcsec).value
            if isinstance(y, u.Quantity):
                y = y.to(u.arcsec).value
            r = math.sqrt(x * x + y * y)
            theta = math.degrees(math.atan2(y, x))
            zeniths.append(round(r, 6))
            azimuths.append(round(theta, 6))

        self["sources_science", "Zenith"] = zeniths
        self["sources_science", "Azimuth"] = azimuths

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

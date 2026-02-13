"""Config validation against the defaults.yaml schema."""
import os.path as p
import yaml


def _load_defaults():
    """Load defaults.yaml and return the parsed dict."""
    with open(p.join(p.dirname(__file__), "defaults.yaml")) as f:
        return yaml.full_load(f.read())


def validate_config(config, defaults=None):
    """Validate a config dict against the defaults.yaml schema.

    Parameters
    ----------
    config : dict[str, dict[str, Any]]
        The configuration to validate (from ini_parser.parse_ini).
    defaults : dict, optional
        The defaults schema. If None, loads from defaults.yaml.

    Returns
    -------
    issues : list[str]
        List of warning/error strings. Empty list means valid.
    """
    if defaults is None:
        defaults = _load_defaults()

    issues = []

    # Check that known required sections exist
    known_sections = set(defaults.keys())
    config_sections = set(config.keys())

    # Core sections that must always be present
    core_sections = {
        "atmosphere", "telescope", "sources_science", "sources_HO",
        "sensor_science", "sensor_HO", "DM", "RTC",
    }

    # Sections in defaults that have required_keywords
    for section_name, section_defaults in defaults.items():
        if not isinstance(section_defaults, dict):
            continue

        required_keys = section_defaults.get("required_keywords", [])
        if not required_keys:
            continue

        if section_name not in config:
            if section_name in core_sections:
                issues.append(
                    f"ERROR: Missing required section [{section_name}]"
                )
            continue

        # Check required keywords within the section (if section is present)
        for key in required_keys:
            if key not in config[section_name]:
                issues.append(
                    f"ERROR: Missing required key '{key}' in [{section_name}]"
                )

    # Warn on unknown sections (might be newer TIPTOP params like sources_Focus)
    extra_sections = config_sections - known_sections
    for section_name in sorted(extra_sections):
        issues.append(
            f"WARNING: Unknown section [{section_name}] "
            f"(may be a newer TIPTOP parameter)"
        )

    # Check for unknown keys within known sections
    for section_name in config_sections & known_sections:
        section_defaults = defaults[section_name]
        if not isinstance(section_defaults, dict):
            continue

        known_keys = {
            k for k in section_defaults
            if k not in ("description", "required_keywords")
        }
        config_keys = set(config[section_name].keys())
        extra_keys = config_keys - known_keys
        for key in sorted(extra_keys):
            issues.append(
                f"WARNING: Unknown key '{key}' in [{section_name}] "
                f"(may be a newer TIPTOP parameter)"
            )

    # Type checking for key parameters
    _check_types(config, issues)

    return issues


def _check_types(config, issues):
    """Basic type checks for common parameters."""
    # Numeric checks
    numeric_params = [
        ("atmosphere", "Seeing", (int, float)),
        ("atmosphere", "L0", (int, float)),
        ("telescope", "TelescopeDiameter", (int, float)),
        ("telescope", "ObscurationRatio", (int, float)),
        ("telescope", "Resolution", (int, float)),
    ]
    for section, key, expected_types in numeric_params:
        if section in config and key in config[section]:
            val = config[section][key]
            if val is not None and not isinstance(val, expected_types):
                issues.append(
                    f"ERROR: '{key}' in [{section}] should be numeric, "
                    f"got {type(val).__name__}: {val!r}"
                )

    # List checks
    list_params = [
        ("sources_science", "Wavelength"),
        ("sources_science", "Zenith"),
        ("sources_science", "Azimuth"),
        ("DM", "NumberActuators"),
        ("DM", "DmPitchs"),
    ]
    for section, key in list_params:
        if section in config and key in config[section]:
            val = config[section][key]
            if val is not None and not isinstance(val, list):
                issues.append(
                    f"WARNING: '{key}' in [{section}] is typically a list, "
                    f"got {type(val).__name__}: {val!r}"
                )

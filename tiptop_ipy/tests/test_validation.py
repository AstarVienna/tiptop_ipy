"""Tests for the validation module."""
from tiptop_ipy.validation import validate_config


class TestValidateConfig:
    def test_valid_minimal_config(self):
        config = {
            "atmosphere": {"Seeing": 0.8},
            "telescope": {"TelescopeDiameter": 8.0, "ObscurationRatio": 0.14,
                          "Resolution": 320},
            "sources_science": {"Wavelength": [2.2e-6], "Zenith": [0],
                                "Azimuth": [0]},
            "sources_HO": {"Wavelength": [700e-9], "Zenith": [0],
                           "Azimuth": [0]},
            "sources_LO": {"Wavelength": [1650e-9], "Zenith": [0],
                           "Azimuth": [0]},
            "sensor_science": {"PixelScale": 4, "FieldOfView": 256},
            "sensor_HO": {"PixelScale": 220, "FieldOfView": 600,
                          "NumberLenslets": [40], "NumberPhotons": [100]},
            "sensor_LO": {"PixelScale": 30, "FieldOfView": 100,
                          "NumberLenslets": [1], "NumberPhotons": [200]},
            "DM": {"NumberActuators": [40], "DmPitchs": [0.2]},
            "RTC": {"LoopGain_HO": 0.5, "SensorFrameRate_HO": 1000,
                    "LoopDelaySteps_HO": 2},
        }
        issues = validate_config(config)
        errors = [i for i in issues if i.startswith("ERROR")]
        assert len(errors) == 0

    def test_missing_required_section(self):
        config = {"atmosphere": {"Seeing": 0.8}}
        issues = validate_config(config)
        errors = [i for i in issues if "Missing required section" in i]
        assert len(errors) > 0

    def test_missing_required_key(self):
        config = {
            "atmosphere": {},  # missing Seeing
            "telescope": {"TelescopeDiameter": 8.0},
            "sources_science": {"Wavelength": [2.2e-6]},
            "sources_HO": {"Wavelength": [700e-9]},
            "sources_LO": {"Wavelength": [1650e-9]},
            "sensor_science": {"PixelScale": 4},
            "sensor_HO": {"PixelScale": 220},
            "sensor_LO": {"PixelScale": 30},
            "DM": {"NumberActuators": [40]},
            "RTC": {"LoopGain_HO": 0.5},
        }
        issues = validate_config(config)
        assert any("Seeing" in i for i in issues)

    def test_unknown_section_warns(self):
        config = {
            "atmosphere": {"Seeing": 0.8},
            "telescope": {"TelescopeDiameter": 8.0, "ObscurationRatio": 0.14,
                          "Resolution": 320},
            "sources_science": {"Wavelength": [2.2e-6], "Zenith": [0],
                                "Azimuth": [0]},
            "sources_HO": {"Wavelength": [700e-9], "Zenith": [0],
                           "Azimuth": [0]},
            "sources_LO": {"Wavelength": [1650e-9], "Zenith": [0],
                           "Azimuth": [0]},
            "sensor_science": {"PixelScale": 4, "FieldOfView": 256},
            "sensor_HO": {"PixelScale": 220, "FieldOfView": 600,
                          "NumberLenslets": [40], "NumberPhotons": [100]},
            "sensor_LO": {"PixelScale": 30, "FieldOfView": 100,
                          "NumberLenslets": [1], "NumberPhotons": [200]},
            "DM": {"NumberActuators": [40], "DmPitchs": [0.2]},
            "RTC": {"LoopGain_HO": 0.5, "SensorFrameRate_HO": 1000,
                    "LoopDelaySteps_HO": 2},
            "brand_new_section": {"foo": 1},
        }
        issues = validate_config(config)
        assert any("brand_new_section" in i for i in issues)

    def test_type_check_seeing_must_be_numeric(self):
        config = {
            "atmosphere": {"Seeing": "not_a_number"},
            "telescope": {"TelescopeDiameter": 8.0, "ObscurationRatio": 0.14,
                          "Resolution": 320},
            "sources_science": {"Wavelength": [2.2e-6], "Zenith": [0],
                                "Azimuth": [0]},
            "sources_HO": {"Wavelength": [700e-9], "Zenith": [0],
                           "Azimuth": [0]},
            "sources_LO": {"Wavelength": [1650e-9], "Zenith": [0],
                           "Azimuth": [0]},
            "sensor_science": {"PixelScale": 4, "FieldOfView": 256},
            "sensor_HO": {"PixelScale": 220, "FieldOfView": 600,
                          "NumberLenslets": [40], "NumberPhotons": [100]},
            "sensor_LO": {"PixelScale": 30, "FieldOfView": 100,
                          "NumberLenslets": [1], "NumberPhotons": [200]},
            "DM": {"NumberActuators": [40], "DmPitchs": [0.2]},
            "RTC": {"LoopGain_HO": 0.5, "SensorFrameRate_HO": 1000,
                    "LoopDelaySteps_HO": 2},
        }
        issues = validate_config(config)
        assert any("should be numeric" in i for i in issues)

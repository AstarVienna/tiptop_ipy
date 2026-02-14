"""Tests for the TipTop main class."""
import pytest
import astropy.units as u
from tiptop_ipy import TipTop, TipTopConnection


class TestTipTopInit:
    def test_initialised_with_no_template(self):
        tt = TipTop()
        assert isinstance(tt, TipTop)
        assert "DM" in tt.sections

    def test_initialised_with_instrument_name(self):
        tt = TipTop("MICADO_SCAO")
        assert tt._instrument == "MICADO_SCAO"
        assert tt["telescope", "TelescopeDiameter"] == 38.5

    def test_case_insensitive_instrument(self):
        tt = TipTop("micado_scao")
        assert tt["telescope", "TelescopeDiameter"] == 38.5

    def test_instrument_with_ini_extension(self):
        tt = TipTop("MICADO_SCAO.ini")
        assert tt["telescope", "TelescopeDiameter"] == 38.5

    def test_invalid_instrument_raises(self):
        with pytest.raises(FileNotFoundError, match="No template found"):
            TipTop("NONEXISTENT_INSTRUMENT")

    def test_backward_compat_alias(self):
        """TipTopConnection should still work as an alias."""
        tt = TipTopConnection()
        assert isinstance(tt, TipTop)


class TestTupleIndexing:
    def test_getitem_section(self):
        tt = TipTop("MICADO_SCAO")
        atm = tt["atmosphere"]
        assert isinstance(atm, dict)
        assert "Seeing" in atm

    def test_getitem_tuple(self):
        tt = TipTop("MICADO_SCAO")
        seeing = tt["atmosphere", "Seeing"]
        assert isinstance(seeing, (int, float))

    def test_setitem_tuple(self):
        tt = TipTop("MICADO_SCAO")
        tt["atmosphere", "Seeing"] = 0.6
        assert tt["atmosphere", "Seeing"] == 0.6

    def test_setitem_section(self):
        tt = TipTop("MICADO_SCAO")
        tt["atmosphere"] = {"Seeing": 1.2, "L0": 30.0}
        assert tt["atmosphere", "Seeing"] == 1.2
        assert tt["atmosphere", "L0"] == 30.0

    def test_setitem_creates_new_section(self):
        tt = TipTop("MICADO_SCAO")
        tt["new_section", "key"] = 42
        assert tt["new_section", "key"] == 42


class TestDiffAndReset:
    def test_diff_empty_when_unchanged(self):
        tt = TipTop("MICADO_SCAO")
        assert tt.diff() == {}

    def test_diff_shows_changes(self):
        tt = TipTop("MICADO_SCAO")
        original = tt["atmosphere", "Seeing"]
        tt["atmosphere", "Seeing"] = 1.5
        changes = tt.diff()
        assert "atmosphere" in changes
        assert "Seeing" in changes["atmosphere"]
        assert changes["atmosphere"]["Seeing"] == (original, 1.5)

    def test_reset_restores_original(self):
        tt = TipTop("MICADO_SCAO")
        original = tt["atmosphere", "Seeing"]
        tt["atmosphere", "Seeing"] = 1.5
        tt.reset()
        assert tt["atmosphere", "Seeing"] == original
        assert tt.diff() == {}


class TestSaveAndLoad:
    def test_save_and_load_roundtrip(self, tmp_path):
        tt = TipTop("MICADO_SCAO")
        tt["atmosphere", "Seeing"] = 0.5

        path = str(tmp_path / "test.ini")
        tt.save(path)

        tt2 = TipTop(ini_file=path)
        assert tt2["atmosphere", "Seeing"] == pytest.approx(0.5)
        assert tt2["telescope", "TelescopeDiameter"] == pytest.approx(38.5)


class TestRepr:
    def test_repr(self):
        tt = TipTop("MICADO_SCAO")
        r = repr(tt)
        assert "TipTop" in r
        assert "MICADO_SCAO" in r

    def test_repr_html(self):
        tt = TipTop("MICADO_SCAO")
        html = tt._repr_html_()
        assert "<table>" in html
        assert "MICADO_SCAO" in html


class TestListInstruments:
    def test_returns_sorted_list(self):
        instruments = TipTop.list_instruments()
        assert isinstance(instruments, list)
        assert len(instruments) > 0
        assert instruments == sorted(instruments)

    def test_no_ini_extension(self):
        instruments = TipTop.list_instruments()
        for name in instruments:
            assert not name.endswith(".ini")


class TestValidate:
    def test_template_validates(self):
        tt = TipTop("MICADO_SCAO")
        issues = tt.validate()
        errors = [i for i in issues if i.startswith("ERROR")]
        assert len(errors) == 0


class TestWavelengths:
    def test_wavelengths_returns_quantity_in_microns(self):
        tt = TipTop("ERIS")
        wl = tt.wavelengths
        assert isinstance(wl, u.Quantity)
        assert wl.unit == u.um
        assert len(wl) == 1
        assert wl[0].value == pytest.approx(1.65)

    def test_set_wavelengths_plain_floats_assumed_microns(self):
        tt = TipTop("ERIS")
        tt.wavelengths = [1.2, 1.65, 2.2]
        assert len(tt.wavelengths) == 3
        assert tt.wavelengths[0].value == pytest.approx(1.2)
        assert tt["sources_science", "Wavelength"][0] == pytest.approx(1.2e-6)

    def test_set_wavelengths_scalar(self):
        tt = TipTop("ERIS")
        tt.wavelengths = 2.2
        assert len(tt.wavelengths) == 1
        assert tt.wavelengths[0].value == pytest.approx(2.2)

    def test_set_wavelengths_with_quantity(self):
        tt = TipTop("ERIS")
        tt.wavelengths = [500, 700] * u.nm
        assert tt.wavelengths[0].value == pytest.approx(0.5)
        assert tt.wavelengths[1].value == pytest.approx(0.7)
        assert tt["sources_science", "Wavelength"][0] == pytest.approx(500e-9)

    def test_set_wavelengths_angstrom(self):
        tt = TipTop("ERIS")
        tt.wavelengths = 16500 * u.AA
        assert tt.wavelengths[0].value == pytest.approx(1.65)
        assert tt["sources_science", "Wavelength"][0] == pytest.approx(1.65e-6)


class TestPositions:
    def test_positions_returns_quantity_in_arcsec(self):
        tt = TipTop("ERIS")
        x, y = tt.positions
        assert isinstance(x, u.Quantity)
        assert x.unit == u.arcsec
        assert len(x) == 1
        assert x[0].value == pytest.approx(0.0)
        assert y[0].value == pytest.approx(0.0)

    def test_add_off_axis_single_tuple(self):
        tt = TipTop("ERIS")
        tt.add_off_axis_positions((3, 4))
        assert tt["sources_science", "Zenith"] == [pytest.approx(5.0)]
        assert tt["sources_science", "Azimuth"] == [pytest.approx(53.130102, abs=1e-4)]

    def test_add_off_axis_list_of_tuples(self):
        tt = TipTop("ERIS")
        tt.add_off_axis_positions([(0, 0), (5, 5), (-10, 0)])
        x, y = tt.positions
        assert len(x) == 3
        assert x[0].value == pytest.approx(0.0)
        assert x[1].value == pytest.approx(5.0)
        assert y[1].value == pytest.approx(5.0)
        assert x[2].value == pytest.approx(-10.0)
        assert y[2].value == pytest.approx(0.0, abs=1e-10)

    def test_add_off_axis_with_quantities(self):
        tt = TipTop("ERIS")
        tt.add_off_axis_positions([(0 * u.arcsec, 0 * u.arcsec),
                                   (5 * u.arcmin, 0 * u.arcsec)])
        assert tt["sources_science", "Zenith"][1] == pytest.approx(300.0)

    def test_positions_roundtrip(self):
        tt = TipTop("MAVIS")
        x, y = tt.positions
        # Re-set from xy and check roundtrip
        pairs = list(zip(x.value.tolist(), y.value.tolist()))
        tt.add_off_axis_positions(pairs)
        x2, y2 = tt.positions
        assert x2.value == pytest.approx(x.value, abs=1e-4)
        assert y2.value == pytest.approx(y.value, abs=1e-4)


class TestIniContents:
    def test_ini_contents_is_string(self):
        tt = TipTop("MICADO_SCAO")
        ini = tt.ini_contents
        assert isinstance(ini, str)
        assert "[telescope]" in ini
        assert "[atmosphere]" in ini


@pytest.mark.network
class TestServerIntegration:
    """These tests require network access to the ESO TIPTOP server."""

    def test_generate_psf_eris(self):
        tt = TipTop("ERIS")
        result = tt.generate_psf()
        assert result.psf is not None
        assert result.psf.ndim >= 2

    def test_generate_psf_multi_wavelength(self):
        tt = TipTop("ERIS")
        tt["sources_science", "Wavelength"] = [1.2e-6, 1.65e-6, 2.2e-6]
        result = tt.generate_psf()
        assert result.n_wavelengths >= 1

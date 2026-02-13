"""Tests for the TipTopResult class."""
import numpy as np
import pytest
from astropy.io import fits

from tiptop_ipy.result import TipTopResult


def _make_mock_hdulist(n_positions=3, n_wavelengths=1, size=64):
    """Create a mock FITS HDUList matching TIPTOP server output."""
    hdus = [fits.PrimaryHDU()]

    for _ in range(n_wavelengths):
        psf_data = np.random.rand(n_positions, size, size).astype(np.float32)
        hdus.append(fits.ImageHDU(data=psf_data))

    coords = np.random.rand(2, n_positions).astype(np.float32)
    hdus.append(fits.ImageHDU(data=coords))

    return fits.HDUList(hdus)


class TestTipTopResult:
    def test_detect_structure(self):
        hdulist = _make_mock_hdulist(n_positions=3, n_wavelengths=2)
        result = TipTopResult(hdulist)
        assert result.n_wavelengths == 2
        assert result._coord_index == 3

    def test_psf_property(self):
        hdulist = _make_mock_hdulist(n_positions=3)
        result = TipTopResult(hdulist)
        psf = result.psf
        assert psf.shape == (3, 64, 64)

    def test_coordinates(self):
        hdulist = _make_mock_hdulist(n_positions=5)
        result = TipTopResult(hdulist)
        assert result.x.shape == (5,)
        assert result.y.shape == (5,)

    def test_psf_cube(self):
        hdulist = _make_mock_hdulist(n_positions=3, n_wavelengths=3)
        result = TipTopResult(hdulist)
        cube0 = result.psf_cube(0)
        cube2 = result.psf_cube(2)
        assert cube0.shape == (3, 64, 64)
        assert cube2.shape == (3, 64, 64)

    def test_psf_cube_out_of_range(self):
        hdulist = _make_mock_hdulist(n_wavelengths=1)
        result = TipTopResult(hdulist)
        with pytest.raises(IndexError):
            result.psf_cube(5)

    def test_nearest_psf(self):
        hdulist = _make_mock_hdulist(n_positions=3)
        result = TipTopResult(hdulist)
        # nearest_psf should return a 2D array
        psf = result.nearest_psf(result.x[0], result.y[0])
        assert psf.ndim == 2
        assert psf.shape == (64, 64)

    def test_repr(self):
        hdulist = _make_mock_hdulist(n_positions=3, n_wavelengths=2)
        result = TipTopResult(hdulist)
        r = repr(result)
        assert "TipTopResult" in r
        assert "2 wavelength" in r

    def test_repr_html(self):
        hdulist = _make_mock_hdulist(n_positions=3)
        result = TipTopResult(hdulist)
        html = result._repr_html_()
        assert "<table>" in html
        assert "TipTopResult" in html

    def test_writeto(self, tmp_path):
        hdulist = _make_mock_hdulist()
        result = TipTopResult(hdulist)
        path = str(tmp_path / "test.fits")
        result.writeto(path)
        # Verify we can read it back
        loaded = fits.open(path)
        assert len(loaded) == 3
        loaded.close()

    def test_plot(self):
        """Test that plot runs without error (don't display)."""
        matplotlib = pytest.importorskip("matplotlib")
        matplotlib.use("Agg")

        hdulist = _make_mock_hdulist(n_positions=3)
        result = TipTopResult(hdulist)
        fig, ax = result.plot()
        assert fig is not None
        import matplotlib.pyplot as plt
        plt.close(fig)

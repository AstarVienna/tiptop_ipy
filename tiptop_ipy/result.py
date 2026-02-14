"""TipTopResult class wrapping FITS responses from the TIPTOP server."""
import numpy as np
from astropy.io import fits


class TipTopResult:
    """Wraps the FITS HDUList returned by the TIPTOP server.

    Provides convenient access to PSF data, coordinates, plotting,
    and Jupyter display.

    The TIPTOP server returns a FITS file with 5 HDUs:

    - [0] PrimaryHDU — header with config parameters and timing
    - [1] ImageHDU ``PSF CUBE`` — AO-corrected PSF(s), shape (N, FOV, FOV)
    - [2] ImageHDU ``OPEN-LOOP PSF`` — seeing-limited PSF, shape (FOV, FOV)
    - [3] ImageHDU ``DIFFRACTION LIMITED PSF`` — perfect PSF, shape (FOV, FOV)
    - [4] ImageHDU ``Final PSFs profiles`` — radial profiles

    For multi-wavelength requests, there is one PSF CUBE HDU per wavelength.
    Coordinates are stored in the PSF CUBE header cards (CCX0000, CCY0000, ...).

    Parameters
    ----------
    hdulist : fits.HDUList
        The FITS HDUList from the TIPTOP server.

    Attributes
    ----------
    hdulist : fits.HDUList
        The underlying FITS data.
    """

    def __init__(self, hdulist):
        self.hdulist = hdulist
        self._psf_indices = []
        self._open_loop_index = None
        self._diffraction_index = None
        self._profile_index = None
        self._detect_structure()

    def _detect_structure(self):
        """Detect HDU roles using the CONTENT header card.

        Falls back to shape-based heuristics if CONTENT is missing.
        """
        for i, hdu in enumerate(self.hdulist):
            if i == 0:
                continue
            if not isinstance(hdu, fits.ImageHDU) or hdu.data is None:
                continue

            content = hdu.header.get("CONTENT", "").upper()

            if "PSF CUBE" in content:
                self._psf_indices.append(i)
            elif "OPEN-LOOP" in content:
                self._open_loop_index = i
            elif "DIFFRACTION" in content:
                self._diffraction_index = i
            elif "PROFILE" in content:
                self._profile_index = i
            else:
                # Fallback heuristic: 3D data is a PSF cube
                if hdu.data.ndim == 3 and hdu.data.shape[1] == hdu.data.shape[2]:
                    self._psf_indices.append(i)

    def _read_coordinates_from_header(self):
        """Read PSF coordinates from the PSF CUBE header cards."""
        if not self._psf_indices:
            return np.array([]), np.array([])

        header = self.hdulist[self._psf_indices[0]].header
        xs, ys = [], []
        for j in range(10000):
            xkey = f"CCX{j:04d}"
            ykey = f"CCY{j:04d}"
            if xkey in header:
                xs.append(header[xkey])
                ys.append(header[ykey])
            else:
                break

        return np.array(xs, dtype=float), np.array(ys, dtype=float)

    @property
    def psf(self):
        """The PSF image data from the first PSF CUBE HDU.

        For single-position results this is shape (1, H, W).
        For multi-position results this is shape (N, H, W).
        """
        if not self._psf_indices:
            raise ValueError("No PSF data found in FITS file")
        return self.hdulist[self._psf_indices[0]].data

    @property
    def open_loop_psf(self):
        """The seeing-limited (open-loop) PSF, shape (H, W)."""
        if self._open_loop_index is None:
            raise ValueError("No open-loop PSF found in FITS file")
        return self.hdulist[self._open_loop_index].data

    @property
    def diffraction_psf(self):
        """The diffraction-limited PSF, shape (H, W)."""
        if self._diffraction_index is None:
            raise ValueError("No diffraction-limited PSF found in FITS file")
        return self.hdulist[self._diffraction_index].data

    @property
    def x(self):
        """X-axis coordinates of PSF positions in arcsec."""
        xs, _ = self._read_coordinates_from_header()
        return xs

    @property
    def y(self):
        """Y-axis coordinates of PSF positions in arcsec."""
        _, ys = self._read_coordinates_from_header()
        return ys

    @property
    def n_wavelengths(self):
        """Number of wavelength channels (PSF CUBE HDUs)."""
        return len(self._psf_indices)

    @property
    def strehl(self):
        """Strehl ratios for each position (from PSF CUBE header)."""
        if not self._psf_indices:
            return np.array([])
        header = self.hdulist[self._psf_indices[0]].header
        values = []
        for j in range(10000):
            key = f"SR{j:04d}"
            if key in header:
                values.append(header[key])
            else:
                break
        return np.array(values, dtype=float)

    @property
    def fwhm(self):
        """FWHM values in mas for each position (from PSF CUBE header)."""
        if not self._psf_indices:
            return np.array([])
        header = self.hdulist[self._psf_indices[0]].header
        values = []
        for j in range(10000):
            key = f"FWHM{j:04d}"
            if key in header:
                values.append(header[key])
            else:
                break
        return np.array(values, dtype=float)

    def psf_cube(self, wavelength_index=0):
        """Get PSF cube for a specific wavelength index.

        Parameters
        ----------
        wavelength_index : int
            Index into the list of wavelength channels.

        Returns
        -------
        data : np.ndarray
            PSF cube or image.
        """
        if wavelength_index >= len(self._psf_indices):
            raise IndexError(
                f"wavelength_index {wavelength_index} out of range "
                f"(have {len(self._psf_indices)} channels)"
            )
        return self.hdulist[self._psf_indices[wavelength_index]].data

    def nearest_psf(self, x, y, wavelength_index=0):
        """Return the PSF nearest to (x, y) in arcsec.

        Parameters
        ----------
        x, y : float
            Position in arcsec.
        wavelength_index : int
            Which wavelength channel to use.

        Returns
        -------
        psf : np.ndarray
            2D PSF image.
        """
        r2 = (x - self.x) ** 2 + (y - self.y) ** 2
        i = np.argmin(r2)
        cube = self.psf_cube(wavelength_index)
        if cube.ndim == 3:
            return cube[i, :, :]
        return cube  # single PSF

    def plot(self, log_scale=True, wavelength_index=0, position_index=0,
             **kwargs):
        """Quick PSF plot with matplotlib. Works in Jupyter.

        Parameters
        ----------
        log_scale : bool
            Use log10 scaling for the colormap.
        wavelength_index : int
            Which wavelength channel to plot.
        position_index : int
            Which position in the cube to plot.
        **kwargs
            Passed to matplotlib.pyplot.imshow.
        """
        import matplotlib.pyplot as plt

        cube = self.psf_cube(wavelength_index)
        if cube.ndim == 3:
            image = cube[position_index, :, :]
        else:
            image = cube

        plot_data = np.log10(np.clip(image, a_min=1e-20, a_max=None)) if log_scale else image

        fig, ax = plt.subplots(1, 1, figsize=(6, 6))
        defaults = {"origin": "lower", "cmap": "inferno"}
        defaults.update(kwargs)
        im = ax.imshow(plot_data, **defaults)
        plt.colorbar(im, ax=ax, label="log10(flux)" if log_scale else "flux")

        title = "PSF"
        if self.n_wavelengths > 1:
            title += f" [wave {wavelength_index}]"
        if cube.ndim == 3 and cube.shape[0] > 1:
            title += f" [pos {position_index}]"
        ax.set_title(title)
        ax.set_xlabel("pixels")
        ax.set_ylabel("pixels")
        plt.tight_layout()

        return fig, ax

    def writeto(self, filename, overwrite=False):
        """Save FITS to disk.

        Parameters
        ----------
        filename : str
            Output file path.
        overwrite : bool
            Overwrite existing file.
        """
        self.hdulist.writeto(filename, overwrite=overwrite)

    def _repr_html_(self):
        """Rich Jupyter display: PSF thumbnail + HDU summary table."""
        rows = []
        for i, hdu in enumerate(self.hdulist):
            hdu_type = type(hdu).__name__
            shape = str(hdu.data.shape) if hdu.data is not None else "—"
            content = hdu.header.get("CONTENT", "")
            if i == 0:
                content = "Primary header"
            rows.append(f"<tr><td>{i}</td><td>{hdu_type}</td>"
                        f"<td>{shape}</td><td>{content}</td></tr>")

        table = (
            "<table>"
            "<tr><th>HDU</th><th>Type</th><th>Shape</th><th>Content</th></tr>"
            + "".join(rows) +
            "</table>"
        )
        n_pos = len(self.x)
        sr = self.strehl
        sr_str = f", Strehl={sr[0]:.3f}" if len(sr) > 0 else ""
        return (
            f"<b>TipTopResult</b>: {self.n_wavelengths} wavelength(s), "
            f"{n_pos} position(s){sr_str}<br>{table}"
        )

    def __repr__(self):
        n_hdus = len(self.hdulist)
        n_pos = len(self.x)
        sr = self.strehl
        sr_str = f", Strehl={sr[0]:.3f}" if len(sr) > 0 else ""
        return (
            f"TipTopResult({self.n_wavelengths} wavelength(s), "
            f"{n_pos} position(s), {n_hdus} HDUs{sr_str})"
        )

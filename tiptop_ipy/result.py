"""TipTopResult class wrapping FITS responses from the TIPTOP server."""
import numpy as np
from astropy.io import fits


class TipTopResult:
    """Wraps the FITS HDUList returned by the TIPTOP server.

    Provides convenient access to PSF data, coordinates, plotting,
    and Jupyter display.

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
        self._coord_index = None
        self._detect_structure()

    def _detect_structure(self):
        """Detect which HDUs contain PSF data vs coordinate tables.

        Handles both old (3 HDU) and new (5+ HDU) TIPTOP formats.
        The last ImageHDU with shape (N, 2) is the coordinate table.
        All other non-primary ImageHDUs are PSF cubes.
        """
        for i, hdu in enumerate(self.hdulist):
            if i == 0:
                continue  # skip PrimaryHDU
            if isinstance(hdu, fits.ImageHDU) and hdu.data is not None:
                if hdu.data.ndim == 2 and hdu.data.shape[0] == 2:
                    self._coord_index = i
                else:
                    self._psf_indices.append(i)

    @property
    def psf(self):
        """The PSF image data from the first PSF HDU.

        For single-position results this is a 2D array.
        For multi-position results this is a 3D cube (N, H, W).
        """
        if not self._psf_indices:
            raise ValueError("No PSF data found in FITS file")
        return self.hdulist[self._psf_indices[0]].data

    @property
    def x(self):
        """X-axis coordinates in arcsec."""
        if self._coord_index is None:
            raise ValueError("No coordinate data found in FITS file")
        return self.hdulist[self._coord_index].data[0, :]

    @property
    def y(self):
        """Y-axis coordinates in arcsec."""
        if self._coord_index is None:
            raise ValueError("No coordinate data found in FITS file")
        return self.hdulist[self._coord_index].data[1, :]

    @property
    def n_wavelengths(self):
        """Number of wavelength channels (PSF HDU cubes)."""
        return len(self._psf_indices)

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
            role = ""
            if i in self._psf_indices:
                role = "PSF data"
            elif i == self._coord_index:
                role = "Coordinates"
            elif i == 0:
                role = "Header"
            rows.append(f"<tr><td>{i}</td><td>{hdu_type}</td>"
                        f"<td>{shape}</td><td>{role}</td></tr>")

        table = (
            "<table>"
            "<tr><th>HDU</th><th>Type</th><th>Shape</th><th>Content</th></tr>"
            + "".join(rows) +
            "</table>"
        )
        n_pos = len(self.x) if self._coord_index is not None else "?"
        return (
            f"<b>TipTopResult</b>: {self.n_wavelengths} wavelength(s), "
            f"{n_pos} position(s)<br>{table}"
        )

    def __repr__(self):
        n_hdus = len(self.hdulist)
        n_pos = len(self.x) if self._coord_index is not None else "?"
        return (
            f"TipTopResult({self.n_wavelengths} wavelength(s), "
            f"{n_pos} position(s), {n_hdus} HDUs)"
        )

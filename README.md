# TIPTOP-iPy

A wrapper for the ESO TIPTOP microservice

    $ pip install tiptop_ipy

## Basic Usage

List the instrument config files included in this version of TIPTOP-ipy

    >>> import tiptop_ipy

    >>> tiptop_ipy.list_instruments()
    ['ANDES.ini', 'eris.ini', 'eris_lgs.ini', 'HarmoniLTAO_1.ini', 'HarmoniSCAO_1.ini', 'mavis.ini', 'sphere.ini']

Create a ``TipTopConnection`` object and query the TIPTOP server
    
    >>> eris = tiptop_ipy.TipTopConnection("eris.ini")
    >>> eris.query_server()
    >>> eris.writeto("eris.fits", overwrite=True)

The astropy.io.fits.HDUList is held in the ``.hdulist`` property

    >>> eris.hdulist

Query the TIPTOP server directly with the raw string from an existing ``.ini`` config file

    >>> eris_path = tiptop_ipy.list_instruments(include_path=True)[1]
    >>> with open("eris_path") as f:
    >>>     eris_contents = f.read()
    >>>
    >>> hdulist = tiptop_ipy.utils.query_tiptop_server(ini_contents=eris_contents)
    >>> hdulist.writeto("eris.fits", overwrite=True)

## PSF FITS file format

The 

    >>> eris = tiptop_ipy.TipTopConnection("eris.ini")
    >>> eris.query_server()
    >>> eris.hdulist.info()
    No.    Name      Ver    Type      Cards   Dimensions   Format
    0  PRIMARY       1 PrimaryHDU       5   ()      
    1                1 ImageHDU        13   (256, 256, 1)   float64   
    2                1 ImageHDU        10   (1, 2)   float64  


## Documentation

The reader is referred to the [TIPTOP documentation](https://tiptopdoc.readthedocs.io/en/latest/parameterFile.html) for queries regarding the configuration parameters:

User documentation will appear soon for this package. 
In the meantime, feel free to contact me via the [GitHub issues page](https://github.com/astronomyk/tiptop_ipy/issues)
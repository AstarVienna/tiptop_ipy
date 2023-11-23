#!/usr/bin/env python
# It would be super cool to spend time getting the configuration files to work
import argparse
import argparsedirs
import logging
import configparser

from ast import literal_eval
from pathlib import Path
from scalyca import Scala
from tiptop_ipy.tiptop_connection import TipTopConnection
from schema import Schema, Or, And, Optional, SchemaError
import scalyca.colour as c

log = logging.getLogger('root')



class IniParser(configparser.ConfigParser):
    optionxform = str
    _converters = {
        'any': lambda x: literal_eval(x)
    }

    def as_dict(self):
        d = dict(self._sections)
        for k in d:
            d[k] = dict(self._defaults, **d[k])
            d[k].pop('__name__', None)
            for sk in d[k]:
                d[k][sk] = literal_eval(d[k][sk])
        return d


number = Or(int, float)


class TipTop(Scala):
    _app_name = "TipTop ipy"
    _prog = "TipTop ipy"

    _schema = Schema({
        'telescope': {
            'TelescopeDiameter': number,
            Optional('ObscurationRatio'): number,
            'Resolution': int,
            Optional('ZenithAngle'): number,
            Optional('TechnicalFoV'): number,
            Optional('PathPupil'): Or(argparse.FileType('r'), ''),
            Optional('PathStaticOn'): Or(argparse.FileType('r'), ''),
            Optional('PathStaticOff'): Or(argparse.FileType('r'), ''),
            Optional('PathStaticPos'): Or(argparse.FileType('r'), ''),
            'PupilAngle': number,
            Optional('PathApodizer'): Or(argparse.FileType('r'), ''),
            Optional('PathStatModes'): Or(argparse.FileType('r'), ''),
        },
        'atmosphere': {
            'Wavelength': number,
            'Seeing': number,
            'L0': number,
            'Cn2Weights': [number],
            'Cn2Heights': [number],
            'WindSpeed': [number],
            'WindDirection': [number],
            'r0_Value': number,
            'testWindspeed': number,
        },
        'sources_science': {
            'Wavelength': [number],
            'Zenith': [number],
            'Azimuth': [number],
        },
        'sources_HO': {
            'Wavelength': number,
            'Zenith': [number],
            'Azimuth': [number],
            'Height': number,
        },
        'sensor_science': {
            'PixelScale': number,
            'FieldOfView': number,
        },
        'sensor_HO': {
            'WfsType': str,
            'Modulation': number,
            'PixelScale': number,
            'FieldOfView': number,
            'Binning': number,
            'NumberPhotons': [int],
            'SigmaRON': number,
            'Dark': number,
            'SkyBackground': number,
            'Gain': number,
            'ExcessNoiseFactor': number,
            'NumberLenslets': [int],
            'SizeLenslets': [number],
            'NoiseVariance': [Or(None, number)],
        },
        'DM': {
            'NumberActuators': [number],
            'DmPitchs': [number],
            Optional('InfModel'): str,
            Optional('InfCoupling'): [number],
            Optional('DmHeights'): [number],
            Optional('OptimizationZenith'): [number],
            Optional('OptimizationAzimuth'): [number],
            Optional('OptimizationWeight'): [number],
            Optional('OptimizationConditioning'): number,
            Optional('NumberReconstructedLayers'): int,
            Optional('AoArea'): 'circle',
        },
        'RTC': {
            'LoopGain_HO': number,
            'SensorFrameRate_HO': number,
            'LoopDelaySteps_HO': int,
        },
    })

    def add_arguments(self):
        self.add_argument('template', type=argparse.FileType('r'))
        self.add_argument('outdir', action=argparsedirs.WriteableDir)

    def initialize(self):
        parser = IniParser()
        parser.read(self.args.template.name)
        try:
            self._schema.validate(parser.as_dict())
            log.info(f"Successfully validated template file {c.path(self.args.template.name)} against schema")
        except SchemaError as e:
            log.error(f"Could not validate template tile {c.path(self.args.template.name)}!")
            raise e

    def main(self):
        connection = TipTopConnection(self.args.template)
        log.info(f"Making a request with config file {c.path(self.args.template.name)}")
        hdu = connection.query_server()
        outfile = Path(self.args.outdir) / Path(self.args.template.name).with_suffix('.fits').name
        log.info(f"Saving the output to {c.path(outfile)}")
        connection.writeto(outfile, overwrite=True)


if __name__ == "__main__":
    TipTop().run()

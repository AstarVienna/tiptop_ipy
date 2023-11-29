import argparse
from pathlib import Path
from enschema import Schema, Or, And, Optional

from .config import Config



number = Or(int, float)


class TiptopConfig(Config):
    _sensor_schema = Schema({
        'NumberLenslets': [int],
        Optional('SizeLenslets'): [number],
        'PixelScale': number,
        'FieldOfView': int,
        'NumberPhotons': [int],
        Optional('Binning', default=1): int,
        Optional('WfsType'): Or('Shack-Hartmann', 'Pyramid'),
        'SigmaRON': number,
        Optional('Dark'): number,
        Optional('SkyBackground'): number,
        Optional('Gain'): number,
        Optional('ExcessNoiseFactor', default=2.0): number,
        Optional('Dispersion'): [[float]],
        Optional('SpectralBandwidth'): number,
        Optional('ThresholdWCoG'): number,
        Optional('WindowRadiusWCoG'): number,
        Optional('NewValueThrPix'): number,
        Optional('Transmittance'): [number],
        Optional('NoiseVariance'): [Or(None, number)],
        Optional('Modulation', default=None): Or(None, number),
        Optional('Algorithm', default='wcog'): str,
        Optional('Gain', default=1.0): number,
        Optional('SpotFWHM', default=[[0, 0, 0]]): [[number]],
    })
    _source_schema = Schema({
        'Wavelength': number,
        Optional('Zenith'): [number],
        Optional('Azimuth'): [number],
        Optional('Height', default=0): number,
    })

    _schema = Schema({
        'telescope': {
            'TelescopeDiameter': number,
            'Resolution': int,
            'PupilAngle': number,
            Optional('ObscurationRatio'): number,
            Optional('ZenithAngle'): number,
            Optional('TechnicalFoV'): number,
            Optional('PathPupil'): str,
            Optional('PathStaticOn'): str,
            Optional('PathStaticOff'): str,
            Optional('PathStaticPos'): str,
            Optional('PathApodizer'): str,
            Optional('PathStatModes'): str,
        },
        'atmosphere': {
            'Wavelength': number,
            'Seeing': number,
            'L0': number,
            'Cn2Weights': [number],
            'Cn2Heights': [number],
            'WindSpeed': [number],
            'WindDirection': [number],
            Optional('r0_Value'): number,
            Optional('testWindspeed'): number,
        },
        'sources_science': {
            'Wavelength': Or(number, [number]),
            'Zenith': [number],
            'Azimuth': [number],
        },
        'sources_HO': _source_schema,
        Optional('sources_LO'): _source_schema,
        'sensor_science': {
            'PixelScale': number,
            'FieldOfView': number,
            Optional('Binning', default=0): number,
        },
        'sensor_HO': _sensor_schema,
        Optional('sensor_LO'): _sensor_schema,
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
            Optional('LoopGain_HO'): number,
            Optional('SensorFrameRate_HO'): number,
            Optional('LoopDelaySteps_HO'): int,
            Optional('LoopGain_LO'): number,
            Optional('SensorFrameRate_LO'): number,
            Optional('LoopDelaySteps_LO'): int,
            Optional('ResidualError'): None,
        },
    })

    @staticmethod
    def load(path: Path):
        return __class__(Config._load(path))

import argparse
import configparser

import abc
import yaml

from ast import literal_eval
from pathlib import Path


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


class Config(metaclass=abc.ABCMeta):
    _schema = None

    def __init__(self, data: dict):
        self._data = data
        self._schema.validate(self._data)

    @staticmethod
    def _load(path: Path):
        if path.suffix == '.ini':
            parser = IniParser()
            parser.read(path)
            data = parser.as_dict()
        elif path.suffix in ['.yml', '.yaml']:
            data = yaml.safe_load(path)
        else:
            raise ValueError("Can only open .ini and .yaml files")
        return data

    @property
    def data(self):
        return self._data

    def save_yaml(self, path: Path) -> None:
        return yaml.dump(self.data, path)

    def save_ini(self, path: Path) -> None:
        with path.open('w') as f:
            parser = IniParser(self.data)
            parser.write(f, True)

    def to_str(self) -> str:
        ini_str = ""
        for key, sub_dict in self._data.items():
            ini_str += f"[{key}]\n"
            for sub_key, sub_value in sub_dict.items():
                if sub_key not in ["description", "required_keywords"]:
                    safe_value = f"'{sub_value}'" if isinstance(sub_value, str) else sub_value
                    ini_str += f"{sub_key} = {safe_value}\n"
            ini_str += "\n"

        return ini_str

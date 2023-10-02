# It would be super cool to spend time getting the configuration files to work
import argparse

from scalyca import Scala
from tiptop_ipy.tiptop_connection import TipTopConnection
import logging


log = logging.getLogger('root')
log.setLevel(logging.DEBUG)

class TipTop(Scala):
    app_name = "TIPTOP wrapper"

    def add_arguments(self):
        self.argparser.add_argument('template', type=argparse.FileType('r'))

    def main(self):
        connection = TipTopConnection(self.args.template)
        connection.query_server()


if __name__ == "__main__":
    TipTop().run()
import os
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsProcessingProvider
from cuuatsalg.algorithms import CopyNetworkAttributes

plugin_path = os.path.dirname(__file__)


class CuuatsAlgorithmProvider(QgsProcessingProvider):

    def __init__(self):
        super().__init__()

    def id(self):
        return 'cuuats'

    def name(self):
        return 'CUUATS'

    def icon(self):
        return QIcon(self.svgIconPath())

    def svgIconPath(self):
        return os.path.join(plugin_path, 'images', 'cuuats.svg')

    def loadAlgorithms(self):
        algs = [
            CopyNetworkAttributes()
        ]
        for alg in algs:
            self.addAlgorithm(alg)

    def supportsNonFileBasedOutput(self):
        return True

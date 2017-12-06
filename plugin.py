from qgis.core import QgsApplication
from cuuatsalg.provider import CuuatsAlgorithmProvider


class CuuatsAlgorithmsPlugin:

    def __init__(self):
        self.provider = CuuatsAlgorithmProvider()

    def initGui(self):
        QgsApplication.processingRegistry().addProvider(self.provider)

    def unload(self):
        QgsApplication.processingRegistry().removeProvider(self.provider)

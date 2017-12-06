from qgis.core import QgsProcessingAlgorithm
from qgis.PyQt.QtCore import QCoreApplication


class BaseAlgorithm(QgsProcessingAlgorithm):

    def tr(self, string):
        context = self.__class__.__name__
        return QCoreApplication.translate(context, string)

    def createInstance(self):
        return type(self)()

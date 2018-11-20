from qgis.core import \
    QgsProcessingParameterBoolean, \
    QgsProcessingParameterFile, \
    QgsProcessingParameterFolderDestination, \
    QgsProcessingParameterMultipleLayers
from cuuatsalg.algorithms.base import BaseAlgorithm


class ExportWebMap(BaseAlgorithm):
    TEMPLATE = 'TEMPLATE'
    LAYERS = 'LAYERS'
    TILE = 'TILE'
    MIN_ZOOM = 'MIN_ZOOM'
    MAX_ZOOM = 'MAX_ZOOM'
    FOLDER = 'FOLDER'
    OUTPUT = 'OUTPUT'

    HELP = \
        '''
        '''.replace('\n', '')

    def name(self):
        return 'exportwebmap'

    def displayName(self):
        return self.tr('Export web map')

    def group(self):
        return self.tr('Web')

    def shortHelpString(self):
        return self.tr(self.HELP)

    def tags(self):
        tags = [
            'web',
            'map',
            'internet',
            'online',
            'interactive',
            'Mapbox GL'
        ]
        return self.tr(','.join(tags)).split(',')

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFile(
            self.TEMPLATE,
            self.tr('Template folder'),
            QgsProcessingParameterFile.Behavior.Folder))

        self.addParameter(QgsProcessingParameterMultipleLayers(
            self.LAYERS,
            self.tr('Layers')))

        self.addParameter(QgsProcessingParameterBoolean(
            self.TILE,
            self.tr('Split layers into tiles'),
            True))

        self.addParameter(QgsProcessingParameterBoolean(
            self.MIN_ZOOM,
            self.tr('Minimum tile zoom level'),
            defaultValue=10,
            minValue=0,
            maxValue=22))

        self.addParameter(QgsProcessingParameterBoolean(
            self.MAX_ZOOM,
            self.tr('Maximum tile zoom level'),
            defaultValue=14,
            minValue=0,
            maxValue=22))

        self.addParameter(QgsProcessingParameterFolderDestination(
            self.FOLDER,
            self.tr('Destination folder')))

    def _sanitize(self, name, camel_case=False):
        """
        Sanitize strings for use in file and folder names.
        """

        if camel_case:
            return self.NO_SPACES.sub('', name.title())
        return self.ALLOW_SPACES.sub('', name)

    def processAlgorithm(self, parameters, context, feedback):
        template_dir = self.parameterAsFile(parameters, self.TEMPLATE, context)
        layers = self.parameterAsLayerList(parameters, self.LAYERS, context)
        tile = self.parameterAsBool(parameters, self.TILE, context)
        min_zoom = self.parameterAsInt(parameters, self.MIN_ZOOM, context)
        max_zoom = self.parameterAsInt(parameters, self.MAX_ZOOM, context)
        out_dir = self.parameterAsFile(parameters, self.FOLDER, context)

        return {self.OUTPUT: ''}

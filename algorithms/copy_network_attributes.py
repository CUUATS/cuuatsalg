from qgis.core import QgsProcessing, QgsProcessingParameterFeatureSource, \
    QgsProcessingParameterField, QgsProcessingParameterEnum, \
    QgsProcessingParameterNumber
from cuuatsalg.algorithms.base import BaseAlgorithm


class CopyNetworkAttributes(BaseAlgorithm):
    SOURCE = 'SRC'
    TARGET = 'TARGET'
    FIELDS = 'FIELDS'
    STRATEGY = 'STRATEGY'
    NODE_MAX_DISTANCE = 'NODE_MAX_DISTANCE'
    EDGE_MAX_DISTANCE = 'EDGE_MAX_DISTANCE'
    NODE_NEAREST_DISTANCE = 'NODE_NEAREST_DISTANCE'
    NODE_MAX_ANGLE = 'NODE_MAX_ANGLE'
    NODE_MAX_ANGLE_DISTANCE = 'NODE_MAX_ANGLE_DISTANCE'
    MAX_EDGES = 'MAX_EDGES'

    STRATEGY_AVG = 'STRATEGY_AVG'
    STRATEGY_LONG = 'STRATEGY_LONG'
    STRATEGY_MIN = 'STRATEGY_MIN'
    STRATEGY_MAX = 'STRATEGY_MAX'

    def name(self):
        return 'copynetworkattributes'

    def displayName(self):
        return self.tr('Copy network attributes')

    def group(self):
        return self.tr('Street network')

    def tags(self):
        tags = [
            'street',
            'network',
            'copy',
            'attribute'
        ]
        return self.tr(','.join(tags)).split(',')

    def initAlgorithm(self, config=None):
        self.strategies = [
            (self.STRATEGY_AVG, self.tr('Weighted average')),
            (self.STRATEGY_LONG, self.tr('Longest match')),
            (self.STRATEGY_MIN, self.tr('Minimum')),
            (self.STRATEGY_MAX, self.tr('Maximum')),
        ]

        self.addParameter(QgsProcessingParameterFeatureSource(
            self.SOURCE,
            self.tr('Source network layer'),
            [QgsProcessing.TypeVectorLine]))

        self.addParameter(QgsProcessingParameterFeatureSource(
            self.TARGET,
            self.tr('Target network layer'),
            [QgsProcessing.TypeVectorLine]))

        self.addParameter(QgsProcessingParameterField(
            self.FIELDS,
            self.tr('Fields to copy'),
            parentLayerParameterName=self.SOURCE,
            allowMultiple=True))

        self.addParameter(QgsProcessingParameterEnum(
            self.STRATEGY,
            self.tr('Copy strategy'),
            options=[strategy[1] for strategy in self.strategies],
            allowMultiple=False))

        self.addParameter(QgsProcessingParameterNumber(
            self.NODE_MAX_DISTANCE,
            self.tr('Maximum intersection match distance'),
            minValue=0))

        self.addParameter(QgsProcessingParameterNumber(
            self.EDGE_MAX_DISTANCE,
            self.tr('Maximum segment match distance'),
            minValue=0))

        self.addParameter(QgsProcessingParameterNumber(
            self.MAX_EDGES,
            self.tr('Maximum segments between matched intersections'),
            minValue=1,
            defaultValue=20))

        self.addParameter(QgsProcessingParameterNumber(
            self.NODE_MAX_ANGLE,
            self.tr('Maximum intersection leg angle difference'),
            minValue=0,
            maxValue=180,
            optional=True))

        self.addParameter(QgsProcessingParameterNumber(
            self.NODE_MAX_ANGLE_DISTANCE,
            self.tr('Intersection leg angle distance threshold'),
            minValue=0,
            optional=True))

    def processAlgorithm(self, parameters, context, feedback):
        pass

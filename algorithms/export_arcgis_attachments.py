# import os
# import processing
from qgis.core import QgsProcessingParameterFolderDestination, \
    QgsProcessingParameterString, \
    QgsProcessingParameterField, QgsProcessingParameterFeatureSink, \
    QgsProcessingParameterFeatureSource
from cuuatsalg.algorithms.base import BaseAlgorithm


class ExportArcGISAttachments(BaseAlgorithm):
    SOURCE = 'SOURCE'
    ATTACH = 'ATTACH'
    SOURCE_ID = 'SOURCE_ID'
    ATTACH_ID = 'ATTACH_ID'
    ATTACH_DATA = 'ATTACH_DATA'
    FOLDER = 'FOLDER'
    NAME = 'NAME'
    OUTPUT = 'OUTPUT'
    OUTPUT_ATTACH = 'OUTPUT_ATTACH'

    HELP = \
        ''''''.replace('\n', '')

    def name(self):
        return 'exportarcgisattachments'

    def displayName(self):
        return self.tr('Export ArcGIS attachments')

    def group(self):
        return self.tr('Attachments')

    def shortHelpString(self):
        return self.tr(self.HELP)

    def tags(self):
        tags = [
            'arcgis',
            'attachment',
            'export',
            'image',
            'convert'
        ]
        return self.tr(','.join(tags)).split(',')

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.SOURCE,
            self.tr('Source layer')))

        self.addParameter(QgsProcessingParameterFeatureSource(
            self.ATTACH,
            self.tr('Attachment layer')))

        self.addParameter(QgsProcessingParameterField(
            self.SOURCE_ID,
            self.tr('Source layer ID field'),
            parentLayerParameterName=self.SOURCE))

        self.addParameter(QgsProcessingParameterField(
            self.ATTACH_ID,
            self.tr('Attachment layer source ID field'),
            parentLayerParameterName=self.ATTACH))

        self.addParameter(QgsProcessingParameterField(
            self.ATTACH_DATA,
            self.tr('Attachment layer data field'),
            parentLayerParameterName=self.ATTACH))

        self.addParameter(QgsProcessingParameterFolderDestination(
            self.FOLDER,
            self.tr('Attachment folder')))

        self.addParameter(QgsProcessingParameterString(
            self.NAME,
            self.tr('Path field name')))

        self.addParameter(QgsProcessingParameterFeatureSink(
            self.OUTPUT,
            self.tr('Results layer')))

        self.addParameter(QgsProcessingParameterFeatureSink(
            self.OUTPUT_ATTACH,
            self.tr('Results attachment layer')))

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.SOURCE, context)
        attach = self.parameterAsSource(parameters, self.ATTACH, context)
        source_id = self.parameterAsFields(parameters, self.SOURCE_ID, context)
        attach_id = self.parameterAsFields(parameters, self.ATTACH_ID, context)
        attach_data = self.parameterAsFields(parameters, self.ATTACH_DATA,
                                             context)
        folder = self.parameterAsFile(parameters, self.FOLDER, context)
        name = self.parameterAsString(parameters, self.NAME, context)

        output_sink, output_sink_id = self.parameterAsSink(
            parameters, self.OUTPUT, context, out_fields,
            source.wkbType(), source.sourceCrs())

        attach_sink, attach_sink_id = self.parameterAsSink(
            parameters, self.OUTPUT_ATTACH, context, out_fields,
            source.wkbType(), source.sourceCrs())

        return {self.OUTPUT: output_sink_id}

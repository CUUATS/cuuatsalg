import os
import re
import unicodedata
from PyQt5.QtCore import QVariant
from qgis.core import QgsProcessingParameterFolderDestination, \
    QgsProcessingParameterString, QgsFields, QgsField, QgsFeature, \
    QgsProcessingParameterField, QgsProcessingParameterFeatureSink, \
    QgsProcessingParameterFeatureSource, QgsProcessingParameterBoolean, \
    QgsProcessing, QgsWkbTypes
from cuuatsalg.algorithms.base import BaseAlgorithm


class ExportArcGISAttachments(BaseAlgorithm):
    SOURCE = 'SOURCE'
    ATTACH = 'ATTACH'
    SOURCE_ID = 'SOURCE_ID'
    ATTACH_ID = 'ATTACH_ID'
    ATTACH_DATA = 'ATTACH_DATA'
    FOLDER = 'FOLDER'
    USE_FID = 'USE_FID'
    ID_NAME = 'ID_NAME'
    USE_PATH = 'USE_PATH'
    PATH_NAME = 'PATH_NAME'
    OUTPUT = 'OUTPUT'

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
            self.tr('Source layer'),
            types=[QgsProcessing.TypeVector]))

        self.addParameter(QgsProcessingParameterFeatureSource(
            self.ATTACH,
            self.tr('Attachment layer'),
            types=[QgsProcessing.TypeVector]))

        self.addParameter(QgsProcessingParameterField(
            self.SOURCE_ID,
            self.tr('Source layer ID field'),
            parentLayerParameterName=self.SOURCE))

        self.addParameter(QgsProcessingParameterField(
            self.ATTACH_ID,
            self.tr('Attachment layer source ID field'),
            parentLayerParameterName=self.ATTACH))

        self.addParameter(QgsProcessingParameterFolderDestination(
            self.FOLDER,
            self.tr('Attachment folder')))

        self.addParameter(QgsProcessingParameterBoolean(
            self.USE_FID,
            self.tr('Use feature ID in results'),
            defaultValue=True))

        self.addParameter(QgsProcessingParameterString(
            self.ID_NAME,
            self.tr('ID field name'),
            defaultValue='related_id'))

        self.addParameter(QgsProcessingParameterBoolean(
            self.USE_PATH,
            self.tr('Use full file path in results'),
            defaultValue=False))

        self.addParameter(QgsProcessingParameterString(
            self.PATH_NAME,
            self.tr('Path field name'),
            defaultValue='filename'))

        self.addParameter(QgsProcessingParameterFeatureSink(
            self.OUTPUT,
            self.tr('Results layer')))

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.SOURCE, context)
        attach = self.parameterAsSource(parameters, self.ATTACH, context)
        source_id = self.parameterAsFields(
            parameters, self.SOURCE_ID, context)[0]
        attach_id = self.parameterAsFields(
            parameters, self.ATTACH_ID, context)[0]
        folder = self.parameterAsFile(parameters, self.FOLDER, context)
        use_fid = self.parameterAsBool(parameters, self.USE_FID, context)
        id_name = self.parameterAsString(parameters, self.ID_NAME, context)
        use_path = self.parameterAsBool(parameters, self.USE_PATH, context)
        path_name = self.parameterAsString(parameters, self.PATH_NAME, context)

        out_fields = QgsFields()
        id_type = QVariant.Int
        if not use_fid:
            attach_fields = attach.fields()
            id_type = attach_fields.at(attach_fields.indexOf(attach_id)).type()
        out_fields.append(QgsField(id_name, id_type))
        out_fields.append(QgsField(path_name, QVariant.String))

        output_sink, output_id = self.parameterAsSink(
            parameters, self.OUTPUT, context, out_fields,
            QgsWkbTypes.NoGeometry)

        if use_fid:
            smap = dict([(f[source_id], f.id()) for f in source.getFeatures()])

        for in_feature in attach.getFeatures():
            out_feature = QgsFeature()
            id_value = in_feature[attach_id]
            if use_fid:
                id_value = smap[id_value]

            extension = in_feature['ATT_NAME'].rsplit('.', 1)[-1]
            count = 1
            filename = self.make_filename(id_value, count, extension)
            while os.path.exists(os.path.join(folder, filename)):
                count += 1
                filename = self.make_filename(id_value, count, extension)

            # TODO: Actually create the file.
            path = os.path.join(folder, filename) if use_path else filename
            out_feature.setAttributes(
                [id_value, path])

            output_sink.addFeature(out_feature)

        return {self.OUTPUT: output_id}

    def make_filename(self, id, count, extension):
        id = unicodedata.normalize('NFKD', str(id)).encode(
            'ascii', 'ignore').decode('utf-8')
        id = re.sub('[^\w\s-]', '', id).strip().lower()
        id = re.sub('[-\s]+', '-', id)

        return '%s-%s.%s' % (id, str(count), extension)

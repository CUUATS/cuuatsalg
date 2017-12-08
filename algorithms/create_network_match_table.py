from cuuatsalg.algorithms.base_network import BaseNetworkAlgorithm
from qgis.core import QgsProcessingParameterFeatureSink, QgsFields, QgsField, \
    QgsFeatureSink, QgsFeature
from PyQt5.QtCore import QVariant


class CreateNetworkMatchTable(BaseNetworkAlgorithm):
    OUTPUT = 'OUTPUT'

    def name(self):
        return 'createnetworkmatchtable'

    def displayName(self):
        return self.tr('Create network match table')

    def group(self):
        return self.tr('Street network')

    def tags(self):
        tags = [
            'street',
            'network',
            'match',
            'table'
        ]
        return self.tr(','.join(tags)).split(',')

    def initAlgorithm(self, config=None):
        super().initAlgorithm()

        self.addParameter(QgsProcessingParameterFeatureSink(
            self.OUTPUT,
            self.tr('Output table')))

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.SOURCE, context)
        target = self.parameterAsSource(parameters, self.TARGET, context)

        out_fields = QgsFields()
        for field_name in ['source_fid', 'target_fid']:
            out_fields.append(QgsField(field_name, QVariant.Int))

        sink, output_id = self.parameterAsSink(
            parameters, self.OUTPUT, context, out_fields)
        result = {self.OUTPUT: output_id}

        forward, backward, source_map = self._match(
            source, [], target, parameters, feedback)

        feedback.setProgressText(self.tr('Writing matches table...'))
        feedback_increment = 25.0 / max(len(forward), 1)

        for (out_fid, (source_fid, target_fids)) in enumerate(
                forward.items(), start=1):
            if feedback.isCanceled():
                break
            for target_fid in target_fids:
                out_feature = QgsFeature(out_fid)
                out_feature.setAttributes([source_fid, target_fid])
                sink.addFeature(out_feature, QgsFeatureSink.FastInsert)
            feedback.setProgress(75 + int(out_fid * feedback_increment))

        return result

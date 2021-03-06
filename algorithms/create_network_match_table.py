from cuuatsalg.algorithms.base_network import BaseNetworkAlgorithm
from qgis.core import QgsProcessingParameterFeatureSink, QgsFields, QgsField, \
    QgsFeatureSink, QgsFeature
from PyQt5.QtCore import QVariant


class CreateNetworkMatchTable(BaseNetworkAlgorithm):
    OUTPUT = 'OUTPUT'

    GENERAL_HELP = \
        '''This algorithm matches segments in the source and target networks
        and outputs a table containing the feature IDs of matched segment
        pairs. The matching process is many-to-many, and feature IDs from both
        networks may appear multiple times in the resulting table.
        '''.replace('\n', '')

    def name(self):
        return 'createnetworkmatchtable'

    def displayName(self):
        return self.tr('Create network match table')

    def group(self):
        return self.tr('Street network')

    def shortHelpString(self):
        help = [
            CreateNetworkMatchTable.GENERAL_HELP,
            BaseNetworkAlgorithm.LAYER_PARAMETER_HELP,
            BaseNetworkAlgorithm.INTERSECTION_APPROACH_HELP,
            BaseNetworkAlgorithm.SEGMENT_APPROACH_HELP
        ]
        return self.tr('\n\n'.join(help))

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

        feedback.setProgressText(self.tr('Writing match table...'))
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

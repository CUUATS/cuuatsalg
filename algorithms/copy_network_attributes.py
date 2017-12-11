from numbers import Number
from qgis.core import QgsProcessingParameterField, \
    QgsProcessingParameterEnum, QgsProcessingParameterFeatureSink, \
    QgsProcessingUtils, QgsFields, QgsFeatureSink
from cuuatsalg.algorithms.base_network import BaseNetworkAlgorithm


class CopyNetworkAttributes(BaseNetworkAlgorithm):
    FIELDS = 'FIELDS'
    METHOD = 'METHOD'
    OUTPUT = 'OUTPUT'

    METHOD_AVERAGE = 0
    METHOD_LONGEST = 1
    METHOD_MINIMUM = 2
    METHOD_MAXIMUM = 3

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
        methods = [
            self.tr('Length-weighted average of all matched segment values'),
            self.tr('Value from the longest matched segment'),
            self.tr('Minimum value from the matched segments'),
            self.tr('Maximum value from the matched segments'),
        ]

        self._add_layer_parameters()

        self.addParameter(QgsProcessingParameterField(
            self.FIELDS,
            self.tr('Fields to copy'),
            parentLayerParameterName=self.SOURCE,
            allowMultiple=True))

        self.addParameter(QgsProcessingParameterEnum(
            self.METHOD,
            self.tr('Copy method'),
            options=methods,
            allowMultiple=False))

        self._add_match_option_parameters()

        self.addParameter(QgsProcessingParameterFeatureSink(
            self.OUTPUT,
            self.tr('Result network layer')))

    def _source_fields(self, source, field_names):
        fields = source.fields()
        if not field_names:
            return (list(range(len(fields))), fields)

        idxs = []
        out_fields = QgsFields()
        for field_name in field_names:
            idx = fields.lookupField(field_name)
            if idx < 0:
                continue
            idxs.append(idx)
            out_fields.append(fields.at(idx))

        return (idxs, out_fields)

    def _get_attributes(self, feature, idxs):
        attrs = feature.attributes()
        return [attrs[i] for i in idxs]

    def _clean(self, lists):
        return [[float(v) for v in l if isinstance(v, Number)] for l in lists]

    def _safe_map(self, func, lists):
        return [func(l) if l else None for l in lists]

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.SOURCE, context)
        target = self.parameterAsSource(parameters, self.TARGET, context)
        fields = self.parameterAsFields(parameters, self.FIELDS, context)
        method = self.parameterAsEnum(parameters, self.METHOD, context)

        source_field_idxs, source_fields = self._source_fields(source, fields)
        out_fields = QgsProcessingUtils.combineFields(
            target.fields(), source_fields)
        sink, output_id = self.parameterAsSink(
            parameters, self.OUTPUT, context, out_fields,
            target.wkbType(), target.sourceCrs())
        result = {self.OUTPUT: output_id}

        forward, backward, source_map = self._match(
            source, source_field_idxs, target, parameters, feedback)

        feedback.setProgressText(self.tr('Calculating attribute values...'))
        target_count = source.featureCount()
        feedback_current = 75.0
        feedback_increment = 25.0 / target_count if target_count else 0

        for target_feature in target.getFeatures():
            if feedback.isCanceled():
                break

            attributes = target_feature.attributes()
            matches = backward.get(target_feature.id(), [])
            source_features = [source_map[m] for m in matches]
            if not source_features:
                attributes.extend(len(source_fields) * [None])
            else:
                source_attrs = [self._get_attributes(f, source_field_idxs)
                                for f in source_features]
                if len(source_attrs) == 1:
                    attributes.extend(source_attrs[0])
                elif method == self.METHOD_AVERAGE:
                    lengths = list(self._get_lengths(
                        target_feature, source_features, forward))
                    for (attr_values, field) in zip(
                            zip(*source_attrs), source_fields):
                        weighted_total = 0
                        total_length = 0
                        for (length, value) in zip(lengths, attr_values):
                            if not isinstance(value, Number):
                                continue
                            weighted_total += float(value) * length
                            total_length += length
                        avg = weighted_total / total_length \
                            if total_length > 0 else None
                        if field.typeName() == 'Integer' and avg is not None:
                            avg = int(avg)
                        attributes.append(avg)
                elif method == self.METHOD_LONGEST:
                    lengths = list(self._get_lengths(
                        target_feature, source_features, forward))
                    attributes.extend(
                        source_attrs[lengths.index(max(lengths))])
                elif method == self.METHOD_MINIMUM:
                    attributes.extend(
                        self._safe_map(min, self._clean(zip(*source_attrs))))
                else:
                    attributes.extend(
                        self._safe_map(max, self._clean(zip(*source_attrs))))

            target_feature.setAttributes(attributes)
            sink.addFeature(target_feature, QgsFeatureSink.FastInsert)

            feedback_current += feedback_increment
            feedback.setProgress(feedback_current)

        return result

from numbers import Number
from qgis.core import QgsProcessing, QgsProcessingParameterFeatureSource, \
    QgsProcessingParameterField, QgsProcessingParameterEnum, \
    QgsProcessingParameterNumber, QgsProcessingParameterFeatureSink, \
    QgsProcessingUtils, QgsFeatureRequest, QgsFields, QgsFeatureSink, \
    QgsGeometry, QgsPoint
from cuuatsalg.algorithms.base import BaseAlgorithm
from cuuatsalg.networks import Network, NetworkMatcher


class CopyNetworkAttributes(BaseAlgorithm):
    SOURCE = 'SOURCE'
    TARGET = 'TARGET'
    FIELDS = 'FIELDS'
    METHOD = 'METHOD'
    NODE_MAX_DISTANCE = 'NODE_MAX_DISTANCE'
    EDGE_MAX_DISTANCE = 'EDGE_MAX_DISTANCE'
    MAX_EDGES = 'MAX_EDGES'
    LEG_MAX_ANGLE = 'LEG_MAX_ANGLE'
    LEG_MAX_ANGLE_DISTANCE = 'LEG_MAX_ANGLE_DISTANCE'
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
            self.METHOD,
            self.tr('Copy method'),
            options=methods,
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
            self.tr('Maximum segments to match between matched intersections'),
            minValue=1,
            defaultValue=20))

        self.addParameter(QgsProcessingParameterNumber(
            self.LEG_MAX_ANGLE,
            self.tr('Maximum intersection leg angle difference'),
            minValue=0,
            maxValue=180,
            optional=True))

        self.addParameter(QgsProcessingParameterNumber(
            self.LEG_MAX_ANGLE_DISTANCE,
            self.tr('Intersection leg angle distance threshold'),
            minValue=0,
            optional=True))

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

    def _iter(self, iterator, feedback, start, end):
        increment = float(end - start)
        for pct in iterator:
            feedback.setProgress(start + int(pct * increment))
            if feedback.isCanceled():
                break

    def _matches(self, source, target, parameters, feedback):
        node_max_dist = parameters.get(self.NODE_MAX_DISTANCE, 0)
        edge_max_dist = parameters.get(self.EDGE_MAX_DISTANCE, 0)
        max_edges = parameters.get(self.MAX_EDGES, 0)
        leg_max_angle = parameters.get(self.LEG_MAX_ANGLE, 0)
        leg_max_angle_dist = parameters.get(self.LEG_MAX_ANGLE_DISTANCE, 0)

        feedback.setProgressText(self.tr('Indexing networks...'))
        a_net = Network('source', source, index=False)
        a_build_indexes = a_net.build_indexes(index_nodes=False, iterate=True)
        self._iter(a_build_indexes, feedback, 0, 15)

        b_net = Network('target', target, index=False)
        b_build_indexes = b_net.build_indexes(iterate=True)
        self._iter(b_build_indexes, feedback, 15, 30)

        matcher = NetworkMatcher(
            a_net, b_net,
            node_distance=node_max_dist,
            edge_distance=edge_max_dist,
            leg_angle=leg_max_angle,
            leg_angle_distance=leg_max_angle_dist,
            max_edges=max_edges)

        feedback.setProgressText(self.tr('Matching networks...'))
        match_nodes_nodes = matcher.match_nodes_to_nodes(iterate=True)
        self._iter(match_nodes_nodes, feedback, 30, 45)

        match_nodes_edges = matcher.match_nodes_to_edges(iterate=True)
        self._iter(match_nodes_edges, feedback, 45, 60)

        match_edges_edges = matcher.match_edges_to_edges(iterate=True)
        self._iter(match_edges_edges, feedback, 60, 75)

        return (matcher.ab(), matcher.ba())

    def _get_attributes(self, feature, idxs):
        attrs = feature.attributes()
        return [attrs[i] for i in idxs]

    def _geometry_from_point(self, point):
        return QgsGeometry(QgsPoint(point.x(), point.y()))

    def _get_lengths(self, target_feature, source_features, forward):
        target_geom = target_feature.geometry()
        for source_feature in source_features:
            source_geom = source_feature.geometry()
            target_feature_count = len(forward[source_feature.id()])
            if target_feature_count == 1:
                yield source_geom.length()
            else:
                # If the source edge is shared by multiple target edges, the
                # distance we want is the distance between the closest
                # points to the endpoints of the target edge.
                target_ls = target_geom.constGet()
                target_start = self._geometry_from_point(
                    target_ls.startPoint())
                target_end = self._geometry_from_point(
                    target_ls.endPoint())
                start_location = source_geom.lineLocatePoint(target_start)
                end_location = source_geom.lineLocatePoint(target_end)
                yield abs(start_location - end_location)

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

        forward, backward = self._matches(source, target, parameters, feedback)
        source_request = QgsFeatureRequest().setSubsetOfAttributes(
            source_field_idxs).setFilterFids(list(forward.keys()))
        source_map = dict(
            [(f.id(), f) for f in source.getFeatures(source_request)])

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
                    lengths = self._get_lengths(
                        target_feature, source_features, forward)
                    for attr_values in zip(*source_attrs):
                        weighted_total = 0
                        total_length = 0
                        for (length, value) in zip(lengths, attr_values):
                            if not isinstance(value, Number):
                                continue
                            weighted_total += float(value) * length
                            total_length += length
                        attributes.append(weighted_total / total_length
                                          if total_length > 0 else None)
                elif method == self.METHOD_LONGEST:
                    lengths = self._get_lengths(
                        target_feature, source_features, forward)
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

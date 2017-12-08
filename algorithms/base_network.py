from qgis.core import QgsProcessing, QgsProcessingParameterFeatureSource, \
    QgsProcessingParameterNumber, QgsFeatureRequest, QgsGeometry, QgsPoint
from cuuatsalg.algorithms.base import BaseAlgorithm
from cuuatsalg.networks import Network, NetworkMatcher


class BaseNetworkAlgorithm(BaseAlgorithm):
    SOURCE = 'SOURCE'
    TARGET = 'TARGET'
    NODE_MAX_DISTANCE = 'NODE_MAX_DISTANCE'
    EDGE_MAX_DISTANCE = 'EDGE_MAX_DISTANCE'
    MAX_EDGES = 'MAX_EDGES'
    LEG_MAX_ANGLE = 'LEG_MAX_ANGLE'
    LEG_MAX_ANGLE_DISTANCE = 'LEG_MAX_ANGLE_DISTANCE'

    def _add_layer_parameters(self):
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.SOURCE,
            self.tr('Source network layer'),
            [QgsProcessing.TypeVectorLine]))

        self.addParameter(QgsProcessingParameterFeatureSource(
            self.TARGET,
            self.tr('Target network layer'),
            [QgsProcessing.TypeVectorLine]))

    def _add_match_option_parameters(self):
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

    def initAlgorithm(self, config=None):
        self._add_layer_parameters()
        self.add_match_option_parameters()

    def _iter(self, iterator, feedback, start, end):
        increment = float(end - start)
        for pct in iterator:
            feedback.setProgress(start + int(pct * increment))
            if feedback.isCanceled():
                break

    def _match(self, source, source_field_idxs, target, parameters, feedback):
        node_max_dist = parameters.get(self.NODE_MAX_DISTANCE, 0)
        edge_max_dist = parameters.get(self.EDGE_MAX_DISTANCE, 0)
        max_edges = parameters.get(self.MAX_EDGES, 0)
        leg_max_angle = parameters.get(self.LEG_MAX_ANGLE, 0)
        leg_max_angle_dist = parameters.get(self.LEG_MAX_ANGLE_DISTANCE, 0)

        feedback.setProgressText(self.tr('Indexing networks...'))
        source_request = QgsFeatureRequest().setSubsetOfAttributes(
            source_field_idxs)
        source_map = dict(
            [(f.id(), f) for f in source.getFeatures(source_request)])

        a_net = Network('source', source_map, index=False)
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

        return (matcher.ab(), matcher.ba(), source_map)

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

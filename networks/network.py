import math
from collections import defaultdict
from qgis.core import QgsGeometry, QgsSpatialIndex, QgsFeature, QgsPoint, \
    QgsFeatureRequest


class Network(object):

    def __init__(self, network_id, feature_source, index=True):
        self._id = network_id

        if isinstance(feature_source, dict):
            self._src = None
            self._edge_map = feature_source
        else:
            self._src = feature_source
            self._edge_map = {}

        self._edge_index = QgsSpatialIndex()
        self._edge_nodes = {}

        self._node_map = {}
        self._node_index = QgsSpatialIndex()
        self._node_edges = defaultdict(set)

        if index:
            self.build_indexes()

    def __repr__(self):
        return '<Network %s>' % (str(self._id),)

    def build_indexes(self, index_nodes=True, iterate=False):
        next_node_id = 1
        coords_node = {}
        if self._src is not None:
            request = QgsFeatureRequest()
            request.FetchAttributes = False
            self._edge_map = dict(
                [(f.id(), f) for f in self._src.getFeatures(request)])
        total = len(self._edge_map)

        for (i, (fid, feature)) in enumerate(self._edge_map.items(), start=1):
            fid = feature.id()
            ls = feature.geometry().constGet()
            endpoints = []
            for point in [ls.startPoint(), ls.endPoint()]:
                coords = (point.x(), point.y())
                node_id = coords_node.get(coords, None)

                if node_id is None:
                    node_id = next_node_id
                    next_node_id += 1
                    coords_node[coords] = node_id
                    node_feature = self._make_node_feature(node_id, point)
                    self._node_map[node_id] = node_feature
                    if index_nodes:
                        self._node_index.insertFeature(node_feature)

                endpoints.append(node_id)
                self._node_edges[node_id].add(fid)

            self._edge_index.insertFeature(feature)
            self._edge_nodes[fid] = endpoints

            if iterate:
                yield float(i) / total

    def _make_node_feature(self, fid, point):
        feature = QgsFeature(fid)
        # TODO: Figure out why point.clone() does not work in the line below.
        # (It creates weird issues with the original geometry later in
        # the process.)
        feature.setGeometry(QgsGeometry(QgsPoint(point.x(), point.y())))
        return feature

    def _vertex_id(self, eid, nid):
        if self.get_edge_nids(eid)[0] == nid:
            return 0
        return self.get_edge(eid).geometry().constGet().nCoordinates() - 1

    def _node_angle(self, eid, nid):
        vid = self._vertex_id(eid, nid)
        angle = self.get_edge(eid).geometry().angleAtVertex(vid) \
            * 180 / math.pi
        if vid > 0:
            angle += 180 if angle < 180 else -180
        return angle

    def eids(self):
        return self._edge_map.keys()

    def nids(self):
        return self._node_map.keys()

    def get_edge(self, eid):
        return self._edge_map[eid]

    def get_node(self, nid):
        return self._node_map[nid]

    def find_nids(self, bbox):
        return self._node_index.intersects(bbox)

    def find_eids(self, bbox):
        return self._edge_index.intersects(bbox)

    def get_edge_nids(self, eid):
        return self._edge_nodes[eid]

    def get_node_eids(self, nid):
        return self._node_edges[nid]

    def get_other_nid(self, eid, nid):
        nids = self._edge_nodes[eid]
        if nids[0] == nid:
            return nids[1]
        return nids[0]

    def get_node_angles(self, nid):
        eids = self.get_node_eids(nid)
        return dict([(eid, self._node_angle(eid, nid)) for eid in eids])

    def is_loop(self, eid):
        return len(set(self.get_edge_nids(eid))) == 1

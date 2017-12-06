import math
from collections import defaultdict
from qgis.core import QgsGeometry, QgsSpatialIndex, QgsField, QgsFeature


class Network(object):

    def __init__(self, layer, index_nodes=True):
        self._layer = layer

        self._next_edge_id = -1
        self._edge_map = dict([(f.id(), f) for f in self._layer.getFeatures()])
        self._edge_index = QgsSpatialIndex()
        self._edge_nodes = {}

        self._node_map = {}
        self._node_index = QgsSpatialIndex()
        self._node_edges = defaultdict(set)

        self._build_indexes(index_nodes)

    def __repr__(self):
        return '<Network %s>' % (self._layer.name(),)

    def _build_indexes(self, index_nodes=True):
        next_node_id = 1
        coords_node = {}

        for (fid, feature) in self._edge_map.items():
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
                    node_feature = self._make_feature(
                        node_id, QgsGeometry(point))
                    self._node_map[node_id] = node_feature
                    if index_nodes:
                        self._node_index.insertFeature(node_feature)

                endpoints.append(node_id)
                self._node_edges[node_id].add(fid)

            self._edge_index.insertFeature(feature)
            self._edge_nodes[fid] = endpoints

        self._next_edge_id = fid + 1

    def _has_field(self, field_name):
        return field_name in [f.name() for f in self._layer.fields()]

    def _add_fields(self, fields):
        self._layer.dataProvider().addAttributes(
            [QgsField(fn, ft) for (fn, ft) in fields])

    def _make_feature(self, fid, geometry):
        feature = QgsFeature(fid)
        feature.setGeometry(geometry)
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

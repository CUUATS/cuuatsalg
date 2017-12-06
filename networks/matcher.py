from collections import defaultdict
from cuuatsalg.networks.network import Network


class NetworkMatcher(object):

    @classmethod
    def from_paths(cls, a_path, b_path, **kwargs):
        return cls(Network(a_path, index_nodes=False),
                   Network(b_path), **kwargs)

    def __init__(self, a_network, b_network, **kwargs):
        for net in [a_network, b_network]:
            assert isinstance(net, Network), \
                'arguments must be an instances of Network'

        self._a_network = a_network
        self._b_network = b_network

        self._ab_node_node = {}
        self._b_node_node = set()

        self._ab_node_edge = defaultdict(set)
        self._ba_node_edge = defaultdict(set)
        self._ab_node_edge_dist = {}
        self._ba_node_edge_dist = {}

        self._ab_edge_edge = defaultdict(set)
        self._ba_edge_edge = defaultdict(set)

        self._distance = kwargs.get('distance', 100)
        self._segments = kwargs.get('segments', 20)

    def _networks(self):
        yield (self._a_network, self._b_network)
        yield (self._b_network, self._a_network)

    def _choose(self, network, a, b):
        return a if network == self._a_network else b

    def _match_nodes_to_nodes(self):
        ab = {}
        ba = {}
        a_dist = {}
        b_dist = {}
        default_dist = self._distance + 1

        for a_nid in self._a_network.nids():
            a_node = self._a_network.get_node(a_nid)
            bbox = a_node.geometry().boundingBox().buffered(self._distance)
            for b_nid in self._b_network.find_nids(bbox):
                b_node = self._b_network.get_node(b_nid)
                distance = a_node.geometry().distance(b_node.geometry())
                if distance <= self._distance:
                    if distance < a_dist.get(a_nid, default_dist):
                        ab[a_nid] = b_nid
                        a_dist[a_nid] = distance
                    if distance < b_dist.get(b_nid, default_dist):
                        ba[b_nid] = a_nid
                        b_dist[b_nid] = distance

        for (a_nid, b_nid) in ab.items():
            if ba.get(b_nid, None) == a_nid:
                self._ab_node_node[a_nid] = b_nid
                self._b_node_node.add(b_nid)

    def _match_nodes_to_edges(self):
        for (network, other_network) in self._networks():
            for nid in network.nids():
                node = network.get_node(nid)
                bbox = node.geometry().boundingBox().buffered(self._distance)
                for eid in other_network.find_eids(bbox):
                    edge = other_network.get_edge(eid)
                    distance = node.geometry().distance(edge.geometry())
                    if distance <= self._distance:
                        node_edge = self._choose(
                            network, self._ab_node_edge, self._ba_node_edge)
                        dist = self._choose(network, self._ab_node_edge_dist,
                                            self._ba_node_edge_dist)
                        node_edge[nid].add(eid)
                        dist[(nid, eid)] = distance

    def _match_edges_to_edges(self):
        for (a_nid, b_nid) in self._ab_node_node.items():
            for a_eid in self._a_network.get_node_eids(a_nid):
                if a_eid in self._ab_edge_edge:
                    continue
                a_end_nid = self._a_network.get_other_nid(a_eid, a_nid)
                for b_eid in self._b_network.get_node_eids(b_nid):
                    if b_eid in self._ba_edge_edge:
                        continue
                    b_end_nid = self._b_network.get_other_nid(b_eid, b_nid)
                    if self._find_edge_to_edge_match(
                            a_end_nid, b_end_nid, a_eid, b_eid):
                        break

    def _find_edge_to_edge_match(self, a_end_nid, b_end_nid, a_eid, b_eid):
        for matches in self._iter_edge_matches(
                a_end_nid, b_end_nid, [a_eid], [b_eid], [], self._segments):
            for (a_eid, b_eid) in matches:
                self._ab_edge_edge[a_eid].add(b_eid)
                self._ba_edge_edge[b_eid].add(a_eid)
            # Only find one matching sequence per edge pair.
            return True
        return False

    def _state_endpoint_distance(self, a_nid, b_nid, a_eids, b_eids):
        default_dist = self._distance + 1
        ab_dist = self._ab_node_edge_dist.get(
            (a_nid, b_eids[-1]), default_dist)
        ba_dist = self._ba_node_edge_dist.get(
            (b_nid, a_eids[-1]), default_dist)
        return min(ab_dist, ba_dist)

    def _get_next_states(self, a_nid, b_nid, a_eids, b_eids):
        states = []
        if b_eids[-1] in self._ab_node_edge.get(a_nid, set()) and \
                a_nid not in self._ab_node_node:
            for a_eid in self._a_network.get_node_eids(a_nid):
                if a_eid in a_eids or a_eid in self._ab_edge_edge:
                    continue
                a_other_nid = self._a_network.get_other_nid(a_eid, a_nid)
                a_new_eids = a_eids + [a_eid]
                states.append((a_other_nid, b_nid, a_new_eids, b_eids))
        if a_eids[-1] in self._ba_node_edge.get(b_nid, set()) and \
                b_nid not in self._b_node_node:
            for b_eid in self._b_network.get_node_eids(b_nid):
                if b_eid in b_eids or b_eid in self._ba_edge_edge:
                    continue
                b_other_nid = self._b_network.get_other_nid(b_eid, b_nid)
                b_new_eids = b_eids + [b_eid]
                states.append((a_nid, b_other_nid, a_eids, b_new_eids))

        state_dist = [
            (self._state_endpoint_distance(*state), state) for state in states]
        return [s for (d, s) in sorted(state_dist) if d <= self._distance]

    def _iter_edge_matches(self, a_nid, b_nid, a_eids, b_eids, matches,
                           retries):
        matches = matches + [(a_eids[-1], b_eids[-1])]
        if self._ab_node_node.get(a_nid, None) == b_nid:
            if self._sequence_hausdorff_distance(a_eids, b_eids) <= \
                    self._distance:
                yield matches
        elif retries > 0:
            for (a_nid, b_nid, a_eids, b_eids) in self._get_next_states(
                    a_nid, b_nid, a_eids, b_eids):
                for matches in self._iter_edge_matches(
                        a_nid, b_nid, a_eids, b_eids, matches, retries - 1):
                    yield matches

    def _sequence_hausdorff_distance(self, a_eids, b_eids):
        a_geom = self._combine_feature_geometries(
            [self._a_network.get_edge(eid) for eid in a_eids])
        b_geom = self._combine_feature_geometries(
            [self._b_network.get_edge(eid) for eid in b_eids])

        return a_geom.hausdorffDistance(b_geom)

    def _combine_feature_geometries(self, features):
        geom = features.pop().geometry()
        while features:
            geom = geom.combine(features.pop().geometry())
        return geom

    def match(self):
        self._match_nodes_to_nodes()
        self._match_nodes_to_edges()
        self._match_edges_to_edges()

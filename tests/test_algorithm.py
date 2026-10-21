"""Kern: jede Einheit an von Hand gerechneten Mini-Netzen (DEMO-PLAYBOOK §1b)."""

import pytest

import zvs_algorithm as A

from conftest import AUG, DREIECKE, QUADRAT, adj_of


def _net(name):
    n, pairs, *_ = AUG[name]
    return adj_of(n, pairs)


def test_edges_add_edges_and_adjacency_from_edges():
    adj = adj_of(4, [(0, 1), (1, 2)])
    assert A.edges_of(adj) == ((0, 1), (1, 2)) and A.add_edges(adj, [(2, 3), (0, 1)]) == adj_of(4, [(0, 1), (1, 2), (2, 3)]) and A.adj_from_edges(4, [(1, 0), (2, 1)]) == adj
    assert A.add_edges(adj, []) == adj and A.add_edges(adj, [(0, 3)])[3] == (0,)


def test_components_and_connectivity_by_hand():
    adj = adj_of(6, [(0, 1), (1, 2), (3, 4)])
    assert A.components_without(adj) == [(0, 1, 2), (3, 4), (5,)] and A.components_without(adj, [(1, 2)]) == [(0, 1), (2,), (3, 4), (5,)]
    assert not A.is_connected(adj) and A.is_connected(adj_of(3, [(0, 1), (1, 2)])) and not A.is_connected(adj_of(3, [(0, 1), (1, 2)]), [(0, 1)])


@pytest.mark.parametrize("name", list(AUG))
def test_bridges_blobs_and_leaves_of_every_mini_network(name):
    n, pairs, br, blobs, leaves, new, naive = AUG[name]
    adj = adj_of(n, pairs)
    assert A.bridges(adj) == br
    bt = A.bridge_tree(adj)
    assert bt.bridges == br and bt.blobs == blobs and bt.leaves == leaves
    assert all(bt.owner[v] == i for i, b in enumerate(blobs) for v in b)


def test_bridges_after_removing_an_edge_and_on_disconnected_networks():
    cycle = adj_of(5, [(v, (v + 1) % 5) for v in range(5)])
    assert A.bridges(cycle) == () and A.bridges(cycle, removed={(0, 1)}) == ((0, 4), (1, 2), (2, 3), (3, 4))
    two = adj_of(5, [(0, 1), (2, 3), (3, 4), (2, 4)])
    assert A.bridges(two) == ((0, 1),) and A.is_two_edge_connected(cycle) and not A.is_two_edge_connected(two) and not A.is_two_edge_connected(adj_of(4, [(0, 1), (2, 3)]))
    assert A.bridges(adj_of(2, [(0, 1)])) == ((0, 1),) and A.bridges(adj_of(3, [])) == ()


def test_the_bridge_tree_of_the_lehrbeispiel_is_a_star_with_four_leaves():
    bt = A.bridge_tree(_net("lehrbeispiel"))
    assert bt.tree == ((1, 2, 3, 4), (0,), (0,), (0,), (0,))
    assert A.bridge_tree(_net("kreis6")).leaves == () and A.bridge_tree(_net("kreis6")).tree == ((),)


def test_the_root_of_the_tree_is_the_first_inner_blob_and_leaves_follow_the_depth_first_order():
    # Pfad 0-1-2-3-4 mit einem Zusatzblatt 5 an Standort 2: Blätter 0, 4, 5 in der Reihenfolge der Tiefensuche von der Wurzel (Standort 1) aus
    adj = adj_of(6, [(0, 1), (1, 2), (2, 3), (3, 4), (2, 5)])
    bt = A.bridge_tree(adj)
    assert bt.leaves == (0, 4, 5)


@pytest.mark.parametrize("name", list(AUG))
def test_augmentation_of_every_mini_network(name):
    n, pairs, br, blobs, leaves, new, naive = AUG[name]
    adj = adj_of(n, pairs)
    au = A.augment(adj)
    assert au.edges == new and au.lower_bound == -(-len(leaves) // 2) == len(new) and au.naive_parallel == naive
    assert A.is_two_edge_connected(A.add_edges(adj, au.edges))


def test_leaf_pairing_by_hand():
    au = A.augment(_net("lehrbeispiel"))
    assert au.pairs == ((1, 3), (2, 4)) and au.edges == ((4, 7), (5, 9)) and au.naive_edges == ((4, 6), (5, 9))
    st = A.augment(_net("stern"))
    assert st.pairs == ((1, 2), (2, 3))                                                       # drei Blätter: Blatt 1 mit 2, Blatt 2 mit 3
    five = A.augment(adj_of(11, [(0, 5), (1, 5), (2, 5), (3, 5), (4, 5), (5, 6), (6, 7), (7, 8), (8, 9), (9, 10)]))
    assert len(five.tree.leaves) == 6 and len(five.edges) == 3


def test_the_representative_is_never_the_bridge_end_of_a_bigger_leaf():
    adj = _net("lehrbeispiel")
    bt = A.bridge_tree(adj)
    assert A.representative(bt, 3) == 7 and A.representative(bt, 3, naive=True) == 6 and A.representative(bt, 1) == 4 and A.representative(bt, 1, naive=True) == 4
    fahne = A.bridge_tree(_net("fahne"))
    assert A.representative(fahne, 1) == 2 and A.representative(fahne, 1, naive=True) == 1 and A.representative(fahne, 0) == 0


def test_the_naive_representative_creates_a_parallel_edge_on_the_flag():
    au = A.augment(_net("fahne"))
    assert au.naive_edges == ((0, 1),) and au.naive_parallel == 1 and au.edges == ((0, 2),)


def test_no_bridge_means_no_augmentation():
    au = A.augment(_net("kreis6"))
    assert au.edges == () and au.pairs == () and au.lower_bound == 0 and au.naive_edges == () and au.naive_parallel == 0


def test_minimum_spanning_tree_by_hand():
    n, edges, costs = QUADRAT
    assert A.spanning_tree(n, edges, costs) == (0, 2, 3)                                      # (0,1), (0,3), (1,2): Kosten 3, die Diagonale (Nr. 1) kostet 5
    assert A.spanning_tree(3, [(0, 1), (1, 2), (0, 2)], [2, 2, 1]) == (0, 2)                  # Gleichstand: die kleinere Nummer


def test_minimum_cut_with_weights_by_hand():
    w = [[0, 3, 0, 0], [3, 0, 1, 0], [0, 1, 0, 3], [0, 0, 3, 0]]
    value, side = A.min_cut_weighted(w)
    assert value == pytest.approx(1.0) and side in ((0, 1), (2, 3))
    assert A.min_cut_weighted([[0, 2.5], [2.5, 0]])[0] == pytest.approx(2.5)
    assert A.min_cut_weighted([[0, 0, 1], [0, 0, 0], [1, 0, 0]])[0] == pytest.approx(0.0)
    k4 = [[0 if i == j else 1 for j in range(4)] for i in range(4)]
    assert A.min_cut_weighted(k4)[0] == pytest.approx(3.0)


def test_cover_lp_on_two_triangles_needs_one_lazily_added_cut():
    n, edges, costs = DREIECKE
    lp = A.solve_cover(n, edges, costs)
    assert lp.value == pytest.approx(10.0) and lp.integral and A.chosen_edges(lp) == (0, 2, 3, 4, 5, 7)           # der Kreis 0-1-2-3-4-5: vier Dreiecksleitungen und beide Verbindungen
    assert len(lp.cuts) == 1 and lp.cuts[0] in ((0, 1, 2), (3, 4, 5)) and lp.rounds == 2                          # ohne den Schnitt wären die Verbindungen 0 und die Kosten 6
    ex = A.solve_cover(n, edges, costs, integer=True)
    assert ex.value == pytest.approx(10.0) and A.chosen_edges(ex) == (0, 2, 3, 4, 5, 7) and len(ex.cuts) == 1
    assert A.spanning_tree(n, edges, costs) and sum(costs[i] for i in A.spanning_tree(n, edges, costs)) == 7


def test_cover_on_the_square_with_a_diagonal():
    n, edges, costs = QUADRAT
    ex = A.solve_cover(n, edges, costs, integer=True)
    assert ex.value == pytest.approx(4.0) and A.chosen_edges(ex) == (0, 2, 3, 4) and not ex.cuts and ex.rounds == 1
    lp = A.solve_cover(n, edges, costs)
    assert lp.value == pytest.approx(4.0) and lp.integral and lp.x[1] == pytest.approx(0.0)


def test_cover_with_fixed_edges_counts_their_cost_and_lowers_the_requirement():
    n, edges, costs = DREIECKE
    lp = A.solve_cover(n, edges, costs, fixed=(0, 3))                                          # (0,1) und (1,2) sind gewählt: Standort 1 ist versorgt
    assert lp.x[0] == lp.x[3] == 1.0 and lp.value == pytest.approx(10.0)
    full = A.solve_cover(n, edges, costs, fixed=(0, 2, 3, 4, 5, 7))
    assert full.value == pytest.approx(10.0) and full.rounds == 1 and full.cuts == () and full.x[1] == 0.0


def test_infeasible_candidates_raise():
    with pytest.raises(ValueError):
        A.solve_cover(3, [(0, 1), (1, 2)], [1, 1])


def test_iterative_rounding_on_the_mini_nets():
    n, edges, costs = DREIECKE
    rd = A.iterative_rounding(n, edges, costs)
    assert rd.chosen == (0, 2, 3, 4, 5, 7) and rd.cost == 10 and len(rd.steps) == 6 and rd.lp_first == pytest.approx(10.0) and rd.guarantee_held
    assert all(s.value == pytest.approx(1.0) for s in rd.steps) and [s.edge for s in rd.steps] == [0, 2, 3, 4, 5, 7]            # Gleichstand: die kleinere Nummer
    assert all(s.lp_value == pytest.approx(10.0) for s in rd.steps)
    n, edges, costs = QUADRAT
    rd = A.iterative_rounding(n, edges, costs)
    assert rd.chosen == (0, 2, 3, 4) and rd.cost == 4 and len(rd.steps) == 4


def test_critical_pairs_by_hand():
    n, edges, _c = DREIECKE
    assert A.critical_pairs(adj_of(n, edges)) == (((0, 1), (1, 2)), ((0, 5), (2, 3)), ((3, 4), (4, 5)))
    cycle = adj_of(5, [(v, (v + 1) % 5) for v in range(5)])
    assert len(A.critical_pairs(cycle)) == 10 == A.comb2(5)                                    # in einem Kreis trennt jedes Paar
    n, edges, _c = QUADRAT
    assert A.critical_pairs(adj_of(n, edges)) == (((0, 1), (1, 2)), ((0, 3), (2, 3)))
    k4 = adj_of(4, [(a, b) for a in range(4) for b in range(a + 1, 4)])
    assert A.critical_pairs(k4) == ()                                                          # K4 ist 3-kantenzusammenhängend


def test_critical_pairs_ignore_bridges():
    adj = adj_of(5, [(0, 1), (1, 2), (2, 3), (1, 3), (3, 4)])                                  # Brücken 0-1 und 3-4, Dreieck 1, 2, 3
    assert A.bridges(adj) == ((0, 1), (3, 4)) and A.critical_pairs(adj) == (((1, 2), (1, 3)), ((1, 2), (2, 3)), ((1, 3), (2, 3)))              # alle drei Paare des Dreiecks


def test_comb2_and_isclose():
    assert [A.comb2(m) for m in (0, 1, 2, 5, 66)] == [0, 0, 1, 10, 2145] and A.isclose(1.0, 1.0 + 1e-12) and not A.isclose(1.0, 1.001)

"""Netz-Erzeuger: einfach, zusammenhängend, deterministisch, dokumentierte Größen."""

import math

import pytest

import zvs_constants as C
import zvs_scenario as S

from conftest import FixedRandom


def _simple_connected(inst):
    seen = set()
    for u, v in inst.pairs:
        assert 0 <= u < v < inst.n and (u, v) not in seen
        seen.add((u, v))
    return len(S._components(inst.adj)) == 1


def test_below_stays_in_range_and_shuffle_with_a_fixed_source_is_the_identity():
    assert S._below(FixedRandom(), 5) == 4 and S._below(FixedRandom(), 1) == 0
    assert S._shuffle(range(6), FixedRandom()) == [0, 1, 2, 3, 4, 5]
    assert sorted(S._shuffle(range(10), S.make_rng(3, 1))) == list(range(10))


def test_grid_pairs_and_the_grid_network():
    assert S.grid_pairs(2) == [(0, 1), (0, 2), (1, 3), (2, 3)]
    assert S.grid_pairs(2, 3) == [(0, 1), (0, 3), (1, 2), (1, 4), (2, 5), (3, 4), (4, 5)]
    inst = S.make_instance("grid", 30, seed=1)
    assert inst.n == 30 and inst.m == 49 and sorted(len(a) for a in inst.adj) == [2] * 4 + [3] * 14 + [4] * 12            # 5 Zeilen, 6 Spalten


def test_grid_shape_rounds_to_a_rectangle():
    assert S.grid_shape(12) == (3, 4) and S.grid_shape(16) == (4, 4) and S.grid_shape(64) == (8, 8) and S.grid_shape(37) == (6, 6) and S.grid_shape(8) == (2, 4) and S.grid_shape(9) == (3, 3)
    assert S.make_instance("grid", 12).n == 12 and S.make_instance("grid", 64).n == 64


def test_scalefree_has_the_documented_number_of_links():
    for n in (6, 20, 50):
        inst = S.make_instance("scalefree", n, seed=4)
        assert inst.n == n and inst.m == 3 + 2 * (n - 3)


def test_ring_without_rewiring_is_four_regular():
    pairs = S.ring_pairs(12, FixedRandom(), rewire=0.0)
    assert len(pairs) == 24


def test_verbund_has_the_given_number_of_links_between_every_two_regions():
    for links in (1, 3, 5):
        inst = S.make_instance("verbund", 36, 6.0, links, 2)
        sizes = S.region_sizes(36)
        bounds = [0, sizes[0], sizes[0] + sizes[1], 36]
        region = lambda v: next(i for i in range(3) if bounds[i] <= v < bounds[i + 1])   # noqa: E731
        between = {}
        for u, v in inst.pairs:
            if region(u) != region(v):
                between[(region(u), region(v))] = between.get((region(u), region(v)), 0) + 1
        assert between == {(0, 1): links, (0, 2): links, (1, 2): links}


def test_region_sizes_split_the_network_evenly():
    assert S.region_sizes(10) == [4, 3, 3] and S.region_sizes(9) == [3, 3, 3] and sum(S.region_sizes(47)) == 47


def test_geometric_network_each_location_has_at_least_its_nearest_neighbours():
    pairs, pts = S.geometric_pairs(20, S.make_rng(1, 1), k=3)
    adj = S._adj_from_pairs(20, pairs)
    assert pts.shape == (20, 2) and all(len(a) >= 3 for a in adj) or len(S._components(adj)) == 1
    assert len(S._components(adj)) == 1 and all(0.0 <= x <= 1.0 for x in pts.flatten())
    near = sorted(range(1, 20), key=lambda j: ((pts[j][0] - pts[0][0]) ** 2 + (pts[j][1] - pts[0][1]) ** 2, j))[:3]
    assert all(j in adj[0] for j in near)


def test_textbook_network_by_hand():
    inst = S.make_instance("textbook", 99, seed=5)
    assert inst.n == 10 and inst.m == 11 and inst.pairs == tuple(sorted(S.TEXTBOOK_PAIRS)) and inst.name(0) == "1" and inst.name(9) == "10"
    assert sorted(len(a) for a in inst.adj) == [1, 1, 1, 2, 2, 3, 3, 3, 3, 3]


def test_edge_costs_are_whole_numbers_from_one_to_the_maximum_and_deterministic():
    inst = S.make_instance("random", 20, 4.0, 2, 3)
    c = S.edge_costs(inst, 3)
    assert len(c) == inst.m and all(isinstance(x, int) and 1 <= x <= C.COST_MAX for x in c) and S.edge_costs(inst, 3) == c and S.edge_costs(inst, 4) != c
    assert {1, C.COST_MAX} <= set(S.edge_costs(S.make_instance("random", 80, 10.0, 2, 3), 3))                           # beide Grenzen kommen vor
    assert S.edge_costs(S.make_instance("textbook", 8), 7) == (9, 2, 6, 1, 6, 6, 6, 2, 2, 9, 1)                                   # Regressionswert des Zufalls-Seeds 7


@pytest.mark.parametrize("kind", list(C.KINDS))
def test_every_kind_gives_a_simple_connected_network_that_is_deterministic(kind):
    for seed in (1, 2, 3):
        inst = S.make_instance(kind, 24, 4.0, 2, seed)
        assert _simple_connected(inst) and inst.xy.shape == (inst.n, 2) and abs(inst.xy).max() < 10
        again = S.make_instance(kind, 24, 4.0, 2, seed)
        assert again.pairs == inst.pairs and (again.xy == inst.xy).all()
    if kind not in ("textbook", "grid"):
        assert S.make_instance(kind, 24, 4.0, 2, 1).pairs != S.make_instance(kind, 24, 4.0, 2, 2).pairs


def test_the_network_size_follows_the_setting_except_for_the_grid_and_the_textbook():
    for kind in ("random", "ring", "scalefree", "verbund", "geometric"):
        assert S.make_instance(kind, 37, 4.0, 2, 1).n == 37
    assert S.make_instance("grid", 37).n == 36 and S.make_instance("textbook", 37).n == 10


def test_random_network_has_the_requested_mean_degree():
    inst = S.make_instance("random", 40, 6.0, 2, 1)
    assert inst.m == 120


def test_unknown_kind_and_tiny_networks_are_rejected():
    with pytest.raises(ValueError):
        S.make_instance("sternfoermig", 10)
    with pytest.raises(ValueError):
        S.make_instance("random", 3)


def test_spring_layout_is_finite_scaled_and_deterministic():
    pairs = S.random_connected(15, 25, S.make_rng(1, 1))
    pos1 = S.spring_layout(15, pairs, S.make_rng(9, 9))
    pos2 = S.spring_layout(15, pairs, S.make_rng(9, 9))
    assert pos1.shape == (15, 2) and (pos1 == pos2).all() and math.isfinite(float(pos1.sum())) and abs(pos1).max() <= 1.0 + 1e-9


def test_random_connected_with_a_fixed_source_is_the_path_and_has_the_documented_size():
    assert S.random_connected(5, 4, FixedRandom()) == [(0, 1), (1, 2), (2, 3), (3, 4)]
    assert len(S.random_connected(10, 3, S.make_rng(1, 1))) == 9 and len(S.random_connected(10, 20, S.make_rng(1, 2))) == 20 and len(S.random_connected(5, 999, S.make_rng(1, 3))) == 10


def test_ensure_connected_joins_every_component_to_location_zero():
    assert S._ensure_connected(6, [(1, 2), (3, 4)]) == [(0, 1), (0, 3), (0, 5), (1, 2), (3, 4)]


def test_instance_properties_and_names():
    inst = S.make_instance("random", 12, 4.0, 2, 5)
    assert inst.n == 12 and inst.m == len(inst.pairs) and inst.name(0) == "1" and inst.name(11) == "12" and all(u < v for u, v in inst.pairs)
    assert sum(len(a) for a in inst.adj) == 2 * inst.m

"""Orakel-Test zusammenhang-verstaerken-demo: Brücken, Verstärkung, Spannbaum, Schnitt mit Gewichten, lineares Programm mit nachgeladenen Schnitten, exakte Lösung, Runden und kritische Paare gegen unabhängige Rechenwege (DEMO-PLAYBOOK §12).

Unabhängig: `networkx` (`bridges`, `k_edge_augmentation`, `is_k_edge_connected`, `minimum_spanning_tree`, `stoer_wagner`, `edge_connectivity`), die Aufzählung aller Leitungsmengen und aller 2^(n−1) − 1 Schnitte
und das vollständige lineare Programm mit allen Schnittbedingungen auf einmal (`scipy.optimize.linprog`). Feste Netze (Seeds)."""

import itertools
import random

import numpy as np
import pytest

import zvs_algorithm as A
import zvs_evaluation as ev
import zvs_scenario as S

nx = pytest.importorskip("networkx")
from scipy.optimize import linprog  # noqa: E402

from conftest import AUG, DREIECKE, QUADRAT, adj_of  # noqa: E402


def _nets(count=40, base=4000, n=10):
    kinds = ("random", "scalefree", "verbund", "geometric", "ring", "grid")
    for k in range(count):
        kind = kinds[k % len(kinds)]
        yield S.make_instance(kind, n + k % 3, (2.0, 2.5, 3.5)[k % 3], 1 + k % 2, base + k)


def _graph(n, pairs):
    g = nx.Graph()
    g.add_nodes_from(range(n))
    g.add_edges_from(pairs)
    return g


def test_bridges_equal_networkx():
    for inst in _nets(60):
        assert A.bridges(inst.adj) == tuple(sorted((min(u, v), max(u, v)) for u, v in nx.bridges(_graph(inst.n, inst.pairs)))), (inst.kind, inst.n)
    for name, (n, pairs, br, *_rest) in AUG.items():
        assert A.bridges(adj_of(n, pairs)) == tuple(sorted(tuple(sorted(e)) for e in nx.bridges(_graph(n, pairs)))) == br, name


def test_the_augmentation_has_the_networkx_optimum_size_and_makes_the_network_2_edge_connected():
    for inst in _nets(80):
        g = _graph(inst.n, inst.pairs)
        au = A.augment(inst.adj)
        want = list(nx.k_edge_augmentation(g, k=2)) if not nx.is_k_edge_connected(g, 2) else []
        assert len(au.edges) == len(want), (inst.kind, inst.n)
        h = _graph(inst.n, list(inst.pairs) + list(au.edges))
        assert nx.is_k_edge_connected(h, 2) and h.number_of_edges() == g.number_of_edges() + len(au.edges)           # keine neue Leitung doppelt


def test_the_naive_representative_sometimes_repeats_an_existing_edge_and_ours_never_does():
    repeats = 0
    for inst in _nets(120, 4200, 8):
        au = A.augment(inst.adj)
        existing = set(inst.pairs)
        assert not any(e in existing for e in au.edges)
        repeats += any(e in existing for e in au.naive_edges)
        assert au.naive_parallel == sum(1 for e in au.naive_edges if e in existing or e[0] == e[1])
    assert repeats >= 1


def test_the_minimum_spanning_tree_costs_equal_networkx():
    for inst in _nets(30):
        costs = S.edge_costs(inst, 5)
        g = nx.Graph()
        g.add_nodes_from(range(inst.n))
        for (u, v), c in zip(inst.pairs, costs):
            g.add_edge(u, v, weight=c)
        want = sum(d["weight"] for _u, _v, d in nx.minimum_spanning_tree(g).edges(data=True))
        got = A.spanning_tree(inst.n, inst.pairs, costs)
        assert sum(costs[i] for i in got) == want and len(got) == inst.n - 1


def test_the_weighted_minimum_cut_equals_networkx_stoer_wagner():
    rng = random.Random(8)
    for _ in range(40):
        n = rng.randint(3, 9)
        w = [[0.0] * n for _ in range(n)]
        g = nx.Graph()
        g.add_nodes_from(range(n))
        for u in range(n):
            for v in range(u + 1, n):
                if rng.random() < 0.6:
                    val = round(rng.random() * 3, 3)
                    w[u][v] = w[v][u] = val
                    g.add_edge(u, v, weight=val)
        if not nx.is_connected(g):
            assert A.min_cut_weighted(w)[0] == pytest.approx(0.0)
            continue
        value, side = A.min_cut_weighted(w)
        assert value == pytest.approx(nx.stoer_wagner(g)[0]) and sum(w[u][v] for u in side for v in range(n) if v not in side) == pytest.approx(value)


def _all_cut_lp(n, edges, costs):
    """Das vollständige lineare Programm: alle 2^(n−1) − 1 Schnittbedingungen auf einmal."""
    rows = []
    for mask in range(1, 1 << (n - 1)):
        rows.append([1.0 if ((mask >> u) & 1) != ((mask >> v) & 1) else 0.0 for u, v in edges])
    res = linprog(np.array(costs, dtype=float), A_ub=-np.array(rows), b_ub=-2 * np.ones(len(rows)), bounds=(0, 1), method="highs")
    return res.fun


def test_the_lazy_linear_program_has_the_value_of_the_complete_one_and_a_solution_for_every_cut():
    for inst in _nets(20, 4400, 8):
        c = ev.build_candidate(inst, 3)
        lp = A.solve_cover(inst.n, c.pairs, c.costs)
        assert lp.value == pytest.approx(_all_cut_lp(inst.n, c.pairs, c.costs), abs=1e-6), (inst.kind, inst.n)
        x = lp.x
        for mask in range(1, 1 << (inst.n - 1)):
            crossing = sum(x[i] for i, (u, v) in enumerate(c.pairs) if ((mask >> u) & 1) != ((mask >> v) & 1))
            assert crossing >= 2 - 1e-6


def _brute_2ecss(n, edges, costs):
    best = None
    for r in range(n, len(edges) + 1):
        for subset in itertools.combinations(range(len(edges)), r):
            cost = sum(costs[i] for i in subset)
            if best is not None and cost >= best:
                continue
            if nx.is_k_edge_connected(_graph(n, [edges[i] for i in subset]), 2):
                best = cost
    return best


def test_the_exact_solution_equals_the_enumeration_of_all_edge_sets():
    done = 0
    for inst in _nets(30, 4600, 8):
        c = ev.build_candidate(inst, 4)
        if len(c.pairs) > 13:
            continue
        ex = A.solve_cover(inst.n, c.pairs, c.costs, integer=True)
        assert ex.value == pytest.approx(_brute_2ecss(inst.n, c.pairs, c.costs)), (inst.kind, inst.n)
        assert nx.is_k_edge_connected(_graph(inst.n, [c.pairs[i] for i in A.chosen_edges(ex)]), 2)
        done += 1
    assert done >= 6


def test_the_mini_designs_equal_the_enumeration():
    for n, edges, costs in (DREIECKE, QUADRAT):
        assert A.solve_cover(n, edges, costs, integer=True).value == pytest.approx(_brute_2ecss(n, edges, costs))


def test_iterative_rounding_is_feasible_not_below_the_optimum_and_within_factor_two_of_the_program():
    for inst in _nets(40, 4800, 10):
        c = ev.build_candidate(inst, 6)
        rd = A.iterative_rounding(inst.n, c.pairs, c.costs)
        lp = A.solve_cover(inst.n, c.pairs, c.costs)
        ex = A.solve_cover(inst.n, c.pairs, c.costs, integer=True)
        assert nx.is_k_edge_connected(_graph(inst.n, [c.pairs[i] for i in rd.chosen]), 2)
        assert ex.value - 1e-6 <= rd.cost <= 2 * lp.value + 1e-6 and lp.value <= ex.value + 1e-6 and rd.guarantee_held, (inst.kind, inst.n)


def test_critical_pairs_equal_the_enumeration_of_all_edge_pairs():
    for inst in _nets(24, 5000, 10):
        g = _graph(inst.n, inst.pairs)
        br = set(tuple(sorted(e)) for e in nx.bridges(g))
        want = []
        for e, f in itertools.combinations(sorted(inst.pairs), 2):
            if e in br or f in br:
                continue
            h = g.copy()
            h.remove_edges_from([e, f])
            if not nx.is_connected(h):
                want.append((e, f))
        assert A.critical_pairs(inst.adj) == tuple(sorted(want)), (inst.kind, inst.n)


def test_edge_connectivity_two_is_the_same_as_connected_and_bridgeless():
    for inst in _nets(40):
        g = _graph(inst.n, inst.pairs)
        assert A.is_two_edge_connected(inst.adj) == (nx.edge_connectivity(g) >= 2)

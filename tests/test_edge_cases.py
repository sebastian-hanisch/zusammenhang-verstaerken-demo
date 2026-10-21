"""Randfälle der Kernroutinen: kleinste Netze, Netz ohne Brücke, alle Kandidaten nötig, Gleichstände, Grenzen inklusive (DEMO-PLAYBOOK §12)."""

import dataclasses

import pytest

import zvs_algorithm as A
import zvs_constants as C
import zvs_evaluation as ev
import zvs_scenario as S

from conftest import adj_of


def test_the_smallest_networks():
    adj = adj_of(2, [(0, 1)])
    assert A.bridges(adj) == ((0, 1),) and A.bridge_tree(adj).leaves == (0, 1) and A.is_connected(adj) and not A.is_two_edge_connected(adj)
    tri = adj_of(3, [(0, 1), (1, 2), (0, 2)])
    assert A.is_two_edge_connected(tri) and A.augment(tri).edges == () and A.critical_pairs(tri) == (((0, 1), (0, 2)), ((0, 1), (1, 2)), ((0, 2), (1, 2)))
    assert A.spanning_tree(2, [(0, 1)], [4]) == (0,) and A.spanning_tree(1, [], []) == ()
    single = adj_of(1, [])
    assert A.bridges(single) == () and A.bridge_tree(single).leaves == () and A.is_two_edge_connected(single)


def test_two_single_locations_cannot_be_augmented_without_a_parallel_edge():
    adj = adj_of(2, [(0, 1)])
    au = A.augment(adj)
    assert au.edges == ((0, 1),) and au.naive_parallel == 1                                      # die einzige mögliche Leitung gibt es schon: das Netz ist nicht zu verstärken


def test_a_path_gets_one_closing_edge_and_a_star_needs_half_its_leaves_rounded_up():
    path = adj_of(6, [(v, v + 1) for v in range(5)])
    assert A.augment(path).edges == ((0, 5),)
    for leaves in range(2, 9):
        star = adj_of(leaves + 1, [(0, v) for v in range(1, leaves + 1)])
        au = A.augment(star)
        assert len(au.edges) == -(-leaves // 2) and A.is_two_edge_connected(A.add_edges(star, au.edges)), leaves


def test_a_cover_where_every_candidate_is_needed_picks_them_all():
    cycle = [(v, (v + 1) % 5) for v in range(5)]
    cycle = [(min(u, v), max(u, v)) for u, v in cycle]
    ex = A.solve_cover(5, cycle, [1, 2, 3, 4, 5], integer=True)
    assert A.chosen_edges(ex) == (0, 1, 2, 3, 4) and ex.value == pytest.approx(15.0) and A.solve_cover(5, cycle, [1, 2, 3, 4, 5]).value == pytest.approx(15.0)
    rd = A.iterative_rounding(5, cycle, [1, 2, 3, 4, 5])
    assert rd.cost == 15 and len(rd.steps) == 5


def test_ties_in_costs_still_give_the_optimal_value():
    n = 4
    edges = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
    ex = A.solve_cover(n, edges, [1] * 6, integer=True)
    lp = A.solve_cover(n, edges, [1] * 6)
    assert ex.value == pytest.approx(4.0) and lp.value == pytest.approx(4.0) and A.is_two_edge_connected(A.adj_from_edges(n, [edges[i] for i in A.chosen_edges(ex)]))        # K4: ein Kreis über vier Standorte


def test_the_perturbation_does_not_change_the_true_cost_of_the_linear_program():
    n, edges, costs = 6, [(0, 1), (0, 2), (1, 2), (3, 4), (3, 5), (4, 5), (2, 3), (0, 5)], [1, 1, 1, 1, 1, 1, 3, 3]
    lp = A.solve_cover(n, edges, costs)
    assert lp.value == pytest.approx(sum(c * x for c, x in zip(costs, lp.x)))


def test_validate_reports_every_kind_of_problem_on_tampered_analyses():
    a = ev.analyse(ev.Settings())
    assert ev.validate(a) == []
    aug = a.aug
    broken = dataclasses.replace(aug, edges=aug.edges[:1])
    problems = ev.validate(dataclasses.replace(a, aug=broken))
    assert any("noch eine Brücke" in p for p in problems) and any("nicht ⌈L / 2⌉" in p for p in problems)
    assert any("nicht ⌈L / 2⌉" in p for p in ev.validate(dataclasses.replace(a, aug=dataclasses.replace(aug, lower_bound=aug.lower_bound + 1))))             # nur die Schranke verfälscht
    existing = dataclasses.replace(aug, edges=(a.inst.pairs[0], aug.edges[1]))
    assert any("gibt es schon" in p for p in ev.validate(dataclasses.replace(a, aug=existing)))
    clean = ev.analyse(ev.Settings(kind="grid", n=12, seed=1))
    assert any("keine Brücke, aber die Verstärkung" in p for p in ev.validate(dataclasses.replace(clean, aug=dataclasses.replace(clean.aug, edges=((0, 5),)))))
    assert any("Kandidatennetz ist nicht" in p for p in ev.validate(dataclasses.replace(a, cand=dataclasses.replace(a.cand, pairs=a.cand.pairs[:6], costs=a.cand.costs[:6], added=()))))
    assert any("Spannbaum ist keiner" in p for p in ev.validate(dataclasses.replace(a, mst=a.mst[:-1])))
    lp = a.lp
    assert any("außerhalb von [0, 1]" in p for p in ev.validate(dataclasses.replace(a, lp=dataclasses.replace(lp, x=(2.0,) + lp.x[1:]))))
    assert any("Schnitt unter 2" in p for p in ev.validate(dataclasses.replace(a, lp=dataclasses.replace(lp, x=(0.0,) * len(lp.x)))))
    ex = a.exact
    assert any("teurer als das ganzzahlige" in p for p in ev.validate(dataclasses.replace(a, exact=dataclasses.replace(ex, value=ex.value - 1))))
    assert any("billiger als ein Spannbaum" in p for p in ev.validate(dataclasses.replace(a, exact=dataclasses.replace(ex, value=a.mst_cost - 1), lp=dataclasses.replace(lp, value=0.0))))
    assert any("Kosten des Optimums stimmen nicht" in p for p in ev.validate(dataclasses.replace(a, exact=dataclasses.replace(ex, value=ex.value + 1))))
    assert any("Runden liegt unter dem Optimum" in p for p in ev.validate(dataclasses.replace(a, exact=dataclasses.replace(ex, value=ex.value), rounding=dataclasses.replace(a.rounding, cost=a.rounding.cost - 100))) )
    rd = a.rounding
    assert any("Rundens ist nicht 2-Kanten" in p for p in ev.validate(dataclasses.replace(a, rounding=dataclasses.replace(rd, chosen=rd.chosen[:3]))))
    assert any("Kosten des Rundens stimmen nicht" in p for p in ev.validate(dataclasses.replace(a, rounding=dataclasses.replace(rd, cost=rd.cost + 1))))
    assert any("Doppelten des linearen Programms" in p for p in ev.validate(dataclasses.replace(a, lp=dataclasses.replace(lp, value=rd.cost / 3))))


def test_the_enumeration_limit_is_inclusive_and_the_analysis_is_deterministic():
    assert ev.analyse(ev.Settings(kind="random", n=C.BRUTE_N, seed=3)).exact is not None and ev.analyse(ev.Settings(kind="random", n=C.BRUTE_N + 1, seed=3)).exact is None
    a1, a2 = ev.analyse(ev.Settings(kind="random", n=11, seed=5)), ev.analyse(ev.Settings(kind="random", n=11, seed=5))
    assert a1.aug == a2.aug and a1.cand == a2.cand and a1.mst == a2.mst and a1.lp == a2.lp and a1.exact == a2.exact and a1.rounding == a2.rounding


def test_the_analysis_properties():
    a = ev.analyse(ev.Settings(**C.PRESETS["Redundanz kostet mehr als ein Spannbaum"]))
    assert a.n == 12 and a.m == a.inst.m and a.mst_cost == 21 and a.optimum == 35 and a.design_cost == 35 and a.design == A.chosen_edges(a.exact) and a.rounding_ratio == pytest.approx(36 / 35)
    assert a.cand_adj == A.adj_from_edges(12, a.cand.pairs) and A.is_two_edge_connected(a.design_adj) and a.bridges == ()
    big = ev.analyse(ev.Settings(**C.PRESETS["Größeres Netz: nur das Programm"]))
    assert big.optimum is None and big.rounding_ratio is None and big.design == big.rounding.chosen and big.design_cost == big.rounding.cost


def test_the_candidate_adds_only_the_augmentation_when_the_network_has_bridges():
    inst = S.make_instance("textbook", 10)
    c = ev.build_candidate(inst, 7)
    assert c.added == ((4, 7), (5, 9)) and len(c.pairs) == 13 and set(inst.pairs) <= set(c.pairs) and len(c.costs) == 13 and all(1 <= x <= C.COST_MAX for x in c.costs)
    grid = S.make_instance("grid", 12)
    assert ev.build_candidate(grid, 1).added == () and ev.build_candidate(grid, 1).pairs == grid.pairs


def test_size_boundaries_of_the_regler_range():
    for n in (C.N_MIN, C.N_MAX):
        a = ev.analyse(ev.Settings(kind="random", n=n, deg=C.DEG_MIN, links=C.LINKS_MIN, seed=1))
        assert a.n == n and ev.validate(a) == [], n
        b = ev.analyse(ev.Settings(kind="random", n=n, deg=C.DEG_MAX, links=C.LINKS_MAX, seed=2))
        assert b.n == n and ev.validate(b) == [], n

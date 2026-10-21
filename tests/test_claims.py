"""Jede Zahl im README (Abschnitt „Befunde“) wird hier über dieselben Experimentfunktionen wie in der App nachgerechnet (DEMO-PLAYBOOK §4).

Zähler und Mittel über feste Netze (Verstärken: je Netztyp zwölf Netze mit 16 Standorten und mittlerem Grad 2,5; Entwurf: je Netztyp acht Netze mit 12 Standorten), nie ein einzelner Zufalls-Seed. Die Zahlen der Vormessung im
Einzelplan stammen aus Wegwerfskripten mit anderen Netzen; maßgeblich sind diese hier. Die Ecke des linearen Programms ist durch gestörte Kosten eindeutig (`C.PERTURB`); Zahlen zum Runden hängen an dieser Ecke."""

import pytest

import zvs_constants as C
import zvs_evaluation as ev

from conftest import cached

AUG_LABELS = ["Zufallsnetz, Grad 2,5", "Gitter", "Ring mit Abkürzungen", "Skalenfreies Netz", "Verbundnetz, Grad 2,5", "Kartennetz"]
LABELS = ["Zufallsnetz, Grad 3", "Zufallsnetz, Grad 6", "Gitter", "Ring mit Abkürzungen", "Skalenfreies Netz", "Verbundnetz, Grad 5", "Kartennetz"]


def test_the_augmentation_needs_exactly_half_the_leaves_rounded_up():
    rows = cached("augment_rows")
    assert [r["label"] for r in rows] == AUG_LABELS and all(r["nets"] == 12 and r["n"] == 16 for r in rows)
    assert [r["with_bridges"] for r in rows] == [12, 0, 0, 0, 10, 4] and sum(r["with_bridges"] for r in rows) == 26 and sum(r["nets"] for r in rows) == 72
    assert [r["sum_bridges"] for r in rows] == [58, 0, 0, 0, 14, 7] and sum(r["sum_bridges"] for r in rows) == 79
    assert [r["sum_leaves"] for r in rows] == [48, 0, 0, 0, 20, 8] and sum(r["sum_leaves"] for r in rows) == 76
    assert [r["sum_new"] for r in rows] == [27, 0, 0, 0, 10, 4] and sum(r["sum_new"] for r in rows) == 41 and all(r["ok"] == r["with_bridges"] for r in rows)
    assert all(r["sum_new"] == -(-r["sum_leaves"] // 2) or r["with_bridges"] > 0 for r in rows) and sum(r["sum_new"] for r in rows) >= sum(r["sum_leaves"] for r in rows) / 2


def test_the_naive_representative_repeats_an_existing_edge_in_one_network():
    rows = cached("augment_rows")
    assert [r["naive_nets"] for r in rows] == [0, 0, 0, 0, 0, 1] and sum(r["naive_nets"] for r in rows) == 1


def test_redundancy_costs_about_half_again_as_much_as_a_spanning_tree():
    rows = cached("design_rows")
    assert [r["label"] for r in rows] == LABELS and all(r["nets"] == 8 and r["n"] == 12 for r in rows) and sum(r["nets"] for r in rows) == 56
    assert [r["sum_mst"] for r in rows] == [328, 200, 344, 279, 303, 299, 278] and sum(r["sum_mst"] for r in rows) == 2031
    assert [r["sum_opt"] for r in rows] == [530, 300, 468, 394, 552, 451, 410] and sum(r["sum_opt"] for r in rows) == 3105
    ratios = [r["sum_opt"] / r["sum_mst"] for r in rows]
    assert [round(x, 2) for x in ratios] == [1.62, 1.5, 1.36, 1.41, 1.82, 1.51, 1.47] and round(3105 / 2031, 2) == 1.53


def test_the_linear_program_is_almost_integral_and_the_gap_is_small():
    rows = cached("design_rows")
    assert [round(r["sum_lp"], 1) for r in rows] == [530.0, 300.0, 467.5, 392.0, 551.0, 451.0, 410.0] and round(sum(r["sum_lp"] for r in rows), 1) == 3101.5
    assert [r["lp_integral"] for r in rows] == [8, 6, 7, 4, 6, 8, 8] and sum(r["lp_integral"] for r in rows) == 47
    assert [round(r["max_gap"], 3) for r in rows] == [1.0, 1.0, 1.008, 1.045, 1.016, 1.0, 1.0] and round(max(r["max_gap"] for r in rows), 2) == 1.05
    assert all(r["sum_lp"] <= r["sum_opt"] + 1e-9 for r in rows)


def test_iterative_rounding_is_close_to_the_optimum_and_far_from_the_guarantee():
    rows = cached("design_rows")
    assert [r["round_exact"] for r in rows] == [8, 7, 8, 4, 7, 8, 8] and sum(r["round_exact"] for r in rows) == 50
    assert [r["sum_round"] for r in rows] == [530, 301, 468, 406, 553, 451, 410] and sum(r["sum_round"] for r in rows) == 3119 and round(3119 / 3105, 3) == 1.005
    assert [round(r["max_round"], 3) for r in rows] == [1.0, 1.017, 1.0, 1.095, 1.02, 1.0, 1.0] and round(max(r["max_round"] for r in rows), 2) == 1.1
    assert all(r["half_held"] == r["nets"] for r in rows)                                   # in jedem Schritt gab es eine Leitung mit Wert mindestens ½
    assert all(r["sum_round"] <= 2 * r["sum_lp"] + 1e-6 for r in rows)


def test_only_a_few_cuts_have_to_be_loaded():
    rows = cached("cuts_rows")
    assert all(r["total_cuts"] == 2047 and r["nets"] == 8 for r in rows)
    assert [r["sum_cuts"] for r in rows] == [5, 3, 2, 9, 2, 21, 14] and sum(r["sum_cuts"] for r in rows) == 56 and [r["max_cuts"] for r in rows] == [2, 1, 1, 3, 1, 5, 4]
    assert [r["sum_rounds"] for r in rows] == [13, 11, 10, 17, 10, 29, 22] and sum(r["sum_rounds"] for r in rows) == 112
    assert sum(r["sum_cuts_exact"] for r in rows) == 55


def test_the_cheapest_design_is_far_more_vulnerable_than_the_candidate_network():
    rows = cached("double_rows")
    assert [r["sum_pairs_cand"] for r in rows] == [43, 2, 32, 1, 42, 24, 3] and sum(r["sum_pairs_cand"] for r in rows) == 147 and sum(r["sum_all_cand"] for r in rows) == 15038
    assert [r["sum_pairs_design"] for r in rows] == [242, 482, 446, 454, 169, 360, 460] and sum(r["sum_pairs_design"] for r in rows) == 2613 and sum(r["sum_all_design"] for r in rows) == 4360
    assert round(100 * 147 / 15038, 1) == 1.0 and round(100 * 2613 / 4360) == 60
    assert [r["design_cycle"] for r in rows] == [0, 6, 6, 6, 0, 3, 6] and sum(r["design_cycle"] for r in rows) == 27
    assert [r["sum_m_design"] for r in rows] == [109, 98, 98, 98, 117, 105, 99] and sum(r["sum_m_cand"] for r in rows) == 1285


def test_the_preset_descriptions_hold():
    def a(name):
        return ev.analyse(ev.Settings(**C.PRESETS[name]))
    lehr = a("Lehrbeispiel (Ring mit Anhängseln)")
    assert len(lehr.bridges) == 4 and len(lehr.aug.tree.leaves) == 4 and len(lehr.aug.edges) == 2 and lehr.aug.edges == ((4, 7), (5, 9)) and (lehr.mst_cost, lehr.optimum) == (27, 39)
    rep = a("Der Vertreter ist nicht der Endpunkt")
    assert len(rep.bridges) == 1 and rep.aug.naive_parallel == 1 and rep.aug.edges == ((1, 2),) and rep.aug.naive_edges == ((0, 2),)
    grid = a("Das Gitter braucht nichts")
    assert grid.bridges == () and grid.aug.edges == () and (grid.mst_cost, grid.optimum) == (33, 45)
    red = a("Redundanz kostet mehr als ein Spannbaum")
    assert (red.mst_cost, red.optimum) == (21, 35) and round(red.optimum / red.mst_cost, 2) == 1.67
    miss = a("Das Runden verfehlt das Optimum")
    assert (miss.optimum, miss.rounding.cost) == (46, 49) and round(miss.rounding.cost / miss.optimum, 2) == 1.07 and not miss.lp.integral
    cyc = a("Der Entwurf ist ein einziger Kreis")
    assert len(cyc.design) == 12 and len(cyc.critical_design) == 66 and len(cyc.critical_cand) == 1 and len(cyc.cand.pairs) == 36
    big = a("Größeres Netz: nur das Programm")
    assert big.n == 30 and big.exact is None and round(big.lp_value) == 136 and big.rounding.cost == 138 and pytest.approx(big.lp_value) == 136.0

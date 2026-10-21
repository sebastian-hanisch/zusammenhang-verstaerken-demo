"""Experimente über feste Netze (nie ein einzelner Zufalls-Seed als Befund). Jede Funktion gibt eine Liste von Zeilen (dict) zurück; Verdikte und Abbildungen lesen nur diese Zeilen.

1. `augment_rows`: Verstärken: Brücken, Blätter, neue Leitungen (= ⌈L / 2⌉) und die Vertreterwahl.
2. `design_rows`: Entwerfen: Optimum gegen Spannbaum und lineares Programm, iteratives Runden.
3. `cuts_rows`: wie viele der 2^(n−1) − 1 Schnittbedingungen müssen nachgeladen werden?
4. `double_rows`: Doppelausfälle: kritische Leitungspaare im Kandidatennetz und im billigsten Entwurf."""

from functools import lru_cache

import zvs_algorithm as A
import zvs_constants as C
import zvs_evaluation as ev
import zvs_scenario as S


def kind_label(kind, deg):
    name = C.KIND_NAMES[kind]
    return f"{name}, Grad {deg:g}".replace(".", ",") if kind in ("random", "verbund") else name


def _net(kind, deg, n, seed):
    return S.make_instance(kind, n, deg, 1, seed)


def augment_rows():
    rows = []
    for kind, deg in C.EX_KINDS:
        d = C.EX_AUG_DEG if kind in ("random", "verbund") else deg
        if kind == "random" and deg > 4:
            continue                                            # ein Zufallsnetz mit mittlerem Grad 2,5 genügt
        row = {"kind": kind, "deg": d, "label": kind_label(kind, d), "nets": 0, "n": 0, "with_bridges": 0, "sum_bridges": 0, "sum_leaves": 0, "sum_new": 0, "ok": 0, "naive_nets": 0}
        for seed in range(100000, 100000 + C.EX_AUG_SEEDS):
            inst = _net(kind, d, C.EX_AUG_N, seed)
            aug = A.augment(inst.adj)
            row["nets"] += 1
            row["n"] = inst.n
            if aug.tree.bridges:
                row["with_bridges"] += 1
                row["sum_bridges"] += len(aug.tree.bridges)
                row["sum_leaves"] += len(aug.tree.leaves)
                row["sum_new"] += len(aug.edges)
                row["ok"] += A.is_two_edge_connected(A.add_edges(inst.adj, aug.edges)) and len(aug.edges) == aug.lower_bound == -(-len(aug.tree.leaves) // 2)
                row["naive_nets"] += aug.naive_parallel > 0
        rows.append(row)
    return rows


@lru_cache(maxsize=None)
def _design(kind, deg, seed):
    return ev.analyse(ev.Settings(kind, C.EX_N, deg, 1, seed))


def design_rows():
    rows = []
    for kind, deg in C.EX_KINDS:
        row = {"kind": kind, "deg": deg, "label": kind_label(kind, deg), "nets": 0, "n": C.EX_N, "sum_mst": 0, "sum_opt": 0, "sum_lp": 0.0, "sum_round": 0, "max_round": 1.0, "round_exact": 0, "lp_integral": 0,
               "max_gap": 1.0, "sum_steps": 0, "half_held": 0, "sum_m": 0}
        for seed in C.SWEEP_SEEDS:
            a = _design(kind, deg, seed)
            row["nets"] += 1
            row["sum_mst"] += a.mst_cost
            row["sum_opt"] += a.optimum
            row["sum_lp"] += a.lp_value
            row["sum_round"] += a.rounding.cost
            row["max_round"] = max(row["max_round"], a.rounding.cost / a.optimum)
            row["round_exact"] += a.rounding.cost == a.optimum
            row["lp_integral"] += a.lp.integral
            row["max_gap"] = max(row["max_gap"], a.optimum / a.lp_value)
            row["sum_steps"] += len(a.rounding.steps)
            row["half_held"] += a.rounding.guarantee_held
            row["sum_m"] += len(a.cand.pairs)
        rows.append(row)
    return rows


def cuts_rows():
    rows = []
    for kind, deg in C.EX_KINDS:
        row = {"kind": kind, "deg": deg, "label": kind_label(kind, deg), "nets": 0, "n": C.EX_N, "total_cuts": 2 ** (C.EX_N - 1) - 1, "sum_cuts": 0, "max_cuts": 0, "sum_rounds": 0, "sum_cuts_exact": 0}
        for seed in C.SWEEP_SEEDS:
            a = _design(kind, deg, seed)
            row["nets"] += 1
            row["sum_cuts"] += len(a.lp.cuts)
            row["max_cuts"] = max(row["max_cuts"], len(a.lp.cuts))
            row["sum_rounds"] += a.lp.rounds
            row["sum_cuts_exact"] += len(a.exact.cuts)
        rows.append(row)
    return rows


def double_rows():
    rows = []
    for kind, deg in C.EX_KINDS:
        row = {"kind": kind, "deg": deg, "label": kind_label(kind, deg), "nets": 0, "n": C.EX_N, "sum_pairs_cand": 0, "sum_all_cand": 0, "sum_pairs_design": 0, "sum_all_design": 0, "design_cycle": 0, "sum_m_cand": 0, "sum_m_design": 0}
        for seed in C.SWEEP_SEEDS:
            a = _design(kind, deg, seed)
            md, mc = len(a.design), len(a.cand.pairs)
            row["nets"] += 1
            row["sum_pairs_cand"] += len(a.critical_cand)
            row["sum_all_cand"] += A.comb2(mc)
            row["sum_pairs_design"] += len(a.critical_design)
            row["sum_all_design"] += A.comb2(md)
            row["design_cycle"] += md == a.n and len(a.critical_design) == A.comb2(md)
            row["sum_m_cand"] += mc
            row["sum_m_design"] += md
        rows.append(row)
    return rows

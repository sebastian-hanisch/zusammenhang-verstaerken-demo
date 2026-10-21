"""Zweige der Hauptansicht (Nullspalte-Lehre): Jeder Weg, den die App zeigt, kommt in mindestens einem Preset oder einem festen Netz vor.

Ein Preset, das seine Beschreibung nicht einlöst, fällt in `test_claims.py` auf. Hier: die Zweige und dass jede Abbildung für jeden Zweig gebaut werden kann (kein Fehler, nichtleere Daten)."""

import zvs_algorithm as A
import zvs_constants as C
import zvs_evaluation as ev
import zvs_visualization as V

from conftest import cached


def _all():
    return {name: ev.analyse(ev.Settings(**p)) for name, p in C.PRESETS.items()}


def test_every_preset_validates_clean():
    for name, a in _all().items():
        assert ev.validate(a) == [], name


def test_every_branch_of_the_result_is_reached():
    analyses = list(_all().values())
    assert any(a.bridges for a in analyses) and any(not a.bridges for a in analyses)
    assert any(a.aug.naive_parallel for a in analyses) and any(a.bridges and not a.aug.naive_parallel for a in analyses)
    assert any(a.exact is None for a in analyses) and any(a.exact is not None for a in analyses)
    assert any(a.lp.integral for a in analyses) and any(not a.lp.integral for a in analyses)
    assert any(a.exact and a.rounding.cost == a.optimum for a in analyses) and any(a.exact and a.rounding.cost > a.optimum for a in analyses)
    assert any(a.lp.cuts for a in analyses) and any(not a.lp.cuts for a in analyses)
    assert any(a.cand.added for a in analyses) and any(not a.cand.added for a in analyses)
    assert any(len(a.critical_design) == A.comb2(len(a.design)) for a in analyses) and any(len(a.critical_design) < A.comb2(len(a.design)) for a in analyses)
    assert any(a.critical_net is None for a in analyses) and any(a.critical_net is not None for a in analyses)


def test_the_big_preset_is_the_only_one_without_the_exact_solution():
    assert [name for name, a in _all().items() if a.exact is None] == ["Größeres Netz: nur das Programm"]


def test_every_net_kind_is_used_by_a_preset_or_is_a_known_extra():
    kinds = {p["kind"] for p in C.PRESETS.values()}
    assert kinds >= {"textbook", "random", "grid", "ring", "geometric"}


def test_the_figures_build_for_every_preset():
    for name, a in _all().items():
        inst, cand = a.inst, a.cand
        assert V.build_bridge_map(inst, a.aug.tree).data and V.build_bridge_map(inst, a.aug.tree, a.aug.edges).data and V.build_bridge_map(inst, a.aug.tree, a.aug.naive_edges).data, name
        kw = dict(pairs=cand.pairs, costs=cand.costs, added=cand.added)
        assert V.build_design_map(inst, **kw).data and V.build_design_map(inst, **kw, mst=a.mst).data and V.build_design_map(inst, **kw, x=a.lp.x).data, name
        assert V.build_design_map(inst, **kw, chosen=a.rounding.chosen).data and V.build_design_map(inst, **kw, chosen=a.design, labels=False).data, name
        shown = [cand.pairs[i] for i in a.design]
        assert V.build_pair_map(inst, shown).data
        for pair in (a.critical_design[:2] or ()):
            assert V.build_pair_map(inst, shown, pair).data


def test_the_experiment_figures_build_from_the_cached_rows():
    for fig, rows in ((V.build_augment, "augment_rows"), (V.build_design, "design_rows"), (V.build_cuts, "cuts_rows"), (V.build_double, "double_rows")):
        assert fig(cached(rows)).data

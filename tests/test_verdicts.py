"""Verdikte an von Hand gesetzten Werten (DEMO-PLAYBOOK §12): jede Zahl im Text und jede Schwelle der Art steht hier.

Ein Verdikt ist eine reine Funktion (Art, Text) und bekommt Zeilen, nicht Seeds; so prüft der Test Grenzen und jede genannte Zahl direkt."""

import zvs_constants as C
import zvs_evaluation as ev


def test_formats():
    assert ev._i(1234567) == "1.234.567" and ev._dec(3.0) == "3" and ev._dec(1234.5) == "1.234,5" and ev._dec(0.75) == "0,8" and ev._r(1.5) == "1,50" and ev._r(2.0) == "2"
    assert ev._pct(0.256) == "26" and ev._pct(0.256, 1) == "25,6" and ev._of(3, 1200) == "3 von 1.200"
    assert ev._share(0.0) == "0" and ev._share(0.0098) == "1" and ev._share(0.0016) == "0,2" and ev._share(0.1) == "10" and ev._share(0.6) == "60"
    assert ev._leitungen(1) == "1 Leitung" and ev._leitungen(1000) == "1.000 Leitungen" and ev._bruecken(1) == "1 Brücke" and ev._bruecken(3) == "3 Brücken" and ev._blaetter(1) == "1 Blatt" and ev._blaetter(4) == "4 Blätter"
    assert ev.within_factor_two(10, 5) and not ev.within_factor_two(10.1, 5) and ev.within_factor_two(10.0000001, 5)


def test_verdict_augment_rows_counts_and_warns():
    rows = [{"label": "A", "n": 16, "nets": 4, "with_bridges": 3, "sum_bridges": 9, "sum_leaves": 8, "sum_new": 4, "ok": 3, "naive_nets": 1},
            {"label": "B", "n": 16, "nets": 4, "with_bridges": 1, "sum_bridges": 3, "sum_leaves": 2, "sum_new": 1, "ok": 1, "naive_nets": 0}]
    kind, text = ev.verdict_augment_rows(rows)
    assert kind == "info"
    assert text == ("Von 8 Netzen (2 Netztypen, 16 Standorte, mittlerer Grad 2,5) haben 4 Brücken (12 insgesamt, im Mittel 3 je Netz mit Brücken); die Blätter der Brückenbäume (10) brauchen 5 neue Leitungen, "
                    "in allen 4 Netzen genau ⌈L / 2⌉ und brückenfrei danach. Mit dem kleinsten Standort als Vertreter wäre in 1 von 4 Netzen eine neue Leitung parallel zu einer vorhandenen.")
    rows[0]["naive_nets"] = 0
    assert ev.verdict_augment_rows(rows)[1].endswith("Auch mit dem kleinsten Standort als Vertreter entstand nirgends eine parallele Leitung.")
    rows[1]["ok"] = 0
    assert ev.verdict_augment_rows(rows) == ("warning", "Bei 1 von 4 Netzen mit Brücken ist die Verstärkung nicht brückenfrei oder nicht ⌈L / 2⌉.")


def test_verdict_design_rows_ratios_gap_and_rounding():
    rows = [{"label": "A", "n": 12, "nets": 2, "sum_mst": 10, "sum_opt": 15, "sum_lp": 14.5, "sum_round": 17, "max_round": 1.2, "round_exact": 1, "lp_integral": 1, "max_gap": 1.04},
            {"label": "B", "n": 12, "nets": 2, "sum_mst": 20, "sum_opt": 25, "sum_lp": 25.0, "sum_round": 25, "max_round": 1.0, "round_exact": 2, "lp_integral": 2, "max_gap": 1.0}]
    kind, text = ev.verdict_design_rows(rows)
    assert kind == "info"
    assert text == ("Auf 4 Netzen mit 12 Standorten kostet das Optimum im Mittel (Quotient der Summen) das 1,33-Fache des billigsten Spannbaums (je Netztyp 1,25 bis 1,50). Die Lücke zum linearen Programm ist höchstens 1,04 "
                    "(Summe der Kosten 40 gegen 39,5), seine Lösung ist in 3 von 4 Netzen ganzzahlig. Iteratives Runden trifft das Optimum in 3 von 4 Netzen, kostet im Mittel das 1,05-Fache und im schlechtesten Netz "
                    "das 1,20-Fache (A; Garantie 2).")


def test_verdict_cuts_rows_singular_and_plural():
    rows = [{"label": "A", "n": 12, "nets": 2, "total_cuts": 2047, "sum_cuts": 3, "max_cuts": 2, "sum_rounds": 6}, {"label": "B", "n": 12, "nets": 2, "total_cuts": 2047, "sum_cuts": 1, "max_cuts": 1, "sum_rounds": 4}]
    kind, text = ev.verdict_cuts_rows(rows)
    assert kind == "info"
    assert text == ("Von 2.047 möglichen Schnittbedingungen (bei 12 Standorten) lädt das Verfahren im Mittel 1 Schnitt nach (höchstens 2) und löst das Programm im Mittel 2,5-mal; "
                    "die 12 Gradbedingungen stehen von Anfang an dabei.")
    rows[0]["sum_cuts"] = 5
    assert "im Mittel 1,5 Schnitte nach (höchstens 2)" in ev.verdict_cuts_rows(rows)[1]


def test_verdict_double_rows_shares_and_cycles():
    rows = [{"label": "A", "n": 12, "nets": 2, "sum_pairs_cand": 1, "sum_all_cand": 99, "sum_pairs_design": 30, "sum_all_design": 60, "design_cycle": 1},
            {"label": "B", "n": 12, "nets": 2, "sum_pairs_cand": 1, "sum_all_cand": 101, "sum_pairs_design": 30, "sum_all_design": 60, "design_cycle": 0}]
    kind, text = ev.verdict_double_rows(rows)
    assert kind == "info"
    assert text == ("Im ganzen Kandidatennetz trennen 1 % aller Leitungspaare das Netz, im billigsten Entwurf 50 % (über 4 Netze): Der Entwurf hat weniger Leitungen und ist verwundbarer; ob die Kostenminimierung die Ursache ist, misst der Vergleich nicht. "
                    "In 1 von 4 Netzen ist der Entwurf ein einziger Kreis über alle Standorte (dann trennt jedes Paar).")


def _a(name):
    return ev.analyse(ev.Settings(**C.PRESETS[name]))


def test_verdict_augment_for_the_lehrbeispiel_by_hand():
    kind, text = ev.verdict_augment(_a("Lehrbeispiel (Ring mit Anhängseln)"))
    assert kind == "info"
    assert text == ("**Das Netz hat 4 Brücken**, der Brückenbaum hat 5 Komponenten und 4 Blätter. Jede neue Leitung versorgt höchstens zwei Blätter, also braucht man mindestens ⌈4 / 2⌉ = 2 neue Leitungen; "
                    "die Paarung nach Tiefensuche benutzt 2, danach ist das Netz brückenfrei.")


def test_verdict_augment_branches():
    naive = ev.verdict_augment(_a("Der Vertreter ist nicht der Endpunkt"))[1]
    assert naive.startswith("**Das Netz hat 1 Brücke**, der Brückenbaum hat 2 Komponenten und 2 Blätter.") and "mindestens ⌈2 / 2⌉ = 1 neue Leitung;" in naive
    assert naive.endswith("Mit dem kleinsten Standort als Vertreter wäre eine neue Leitung parallel zu einer vorhandenen.")
    assert ev.verdict_augment(_a("Das Gitter braucht nichts")) == ("info", "**Das Netz hat keine Brücke:** Es ist schon 2-Kanten-zusammenhängend (12 Standorte, 17 Leitungen); nichts zu verstärken.")


def test_verdict_design_branches():
    lehr = ev.verdict_design(_a("Lehrbeispiel (Ring mit Anhängseln)"))[1]
    assert lehr == ("**Der billigste Spannbaum kostet 27.** Das Optimum (2-Kanten-zusammenhängend) kostet 39, also 44 % mehr; das lineare Programm 39 (Lücke 1). "
                    "Iteratives Runden braucht 39 (das Optimum; Garantie 2) in 10 Schritten. Die Lösung des Programms ist ganzzahlig.")
    miss = ev.verdict_design(_a("Das Runden verfehlt das Optimum"))[1]
    assert miss == ("**Der billigste Spannbaum kostet 33.** Das Optimum (2-Kanten-zusammenhängend) kostet 46, also 39 % mehr; das lineare Programm 45 (Lücke 1,02). "
                    "Iteratives Runden braucht 49 (das 1,07-Fache; Garantie 2) in 13 Schritten.")
    frac = ev.verdict_design(_a("Redundanz kostet mehr als ein Spannbaum"))[1]
    assert "das lineare Programm 34,50 (Lücke 1,01)" in frac and "ganzzahlig" not in frac and "(das 1,03-Fache; Garantie 2)" in frac
    big = ev.verdict_design(_a("Größeres Netz: nur das Programm"))[1]
    assert big == ("**Der billigste Spannbaum kostet 93.** Über 14 Standorten gibt es keine exakte Lösung: Das lineare Programm kostet 136 (untere Schranke); iteratives Runden braucht 138, "
                   "höchstens das 1,01-Fache der Schranke (Garantie 2), in 32 Schritten.")


def test_verdict_double_branches():
    assert ev.verdict_double(_a("Lehrbeispiel (Ring mit Anhängseln)"))[1] == ("**Im Entwurf mit 10 Leitungen trennen 45 von 45 Leitungspaaren (100 %) das Netz**, "
                                                                           "im ganzen Kandidatennetz mit 13 Leitungen 8 von 78 (10 %).")
    assert ev.verdict_double(_a("Der Entwurf ist ein einziger Kreis"))[1].endswith("im ganzen Kandidatennetz mit 36 Leitungen 1 von 630 (0,2 %).")
    assert ev.verdict_double(_a("Redundanz kostet mehr als ein Spannbaum"))[1].endswith("im ganzen Kandidatennetz mit 24 Leitungen 0 von 276 (0 %).")
    assert "225 von 496 Leitungspaaren (45 %)" in ev.verdict_double(_a("Größeres Netz: nur das Programm"))[1]


def test_verdict_design_without_the_exact_solution_names_a_rounding_that_meets_the_bound():
    import dataclasses
    a = ev.analyse(ev.Settings(kind="random", n=20, deg=10.0, seed=3))
    assert a.exact is None and a.rounding.cost <= a.lp_value + 1e-6
    text = ev.verdict_design(a)[1]
    assert "genau die Schranke und damit das Optimum" in text and "höchstens das" not in text
    worse = dataclasses.replace(a, rounding=dataclasses.replace(a.rounding, cost=a.rounding.cost + 3))
    assert "Fache der Schranke (Garantie 2)" in ev.verdict_design(worse)[1]

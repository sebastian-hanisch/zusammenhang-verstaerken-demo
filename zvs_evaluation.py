"""Kennzahlen, Prüfung der Ergebnisse und Verdikte. Verdikte sind reine Funktionen (Art, Text): Zahlen kommen aus den Zeilen, nie aus dem Text.

Standorte sind in der Anzeige ab 1 nummeriert (`inst.name`), im Kern ab 0."""

from dataclasses import dataclass, field

import zvs_algorithm as A
import zvs_constants as C
import zvs_scenario as S


@dataclass(frozen=True)
class Settings:
    kind: str = C.DEFAULT_KIND
    n: int = C.DEFAULT_N
    deg: float = C.DEFAULT_DEG
    links: int = C.DEFAULT_LINKS
    seed: int = C.DEFAULT_SEED


@dataclass(frozen=True)
class Candidate:
    pairs: tuple            # alle Kandidatenleitungen (u, v)
    costs: tuple            # Kosten je Leitung (ganze Zahlen 1 bis 9)
    added: tuple            # Leitungen, die zum Netz dazukamen, damit eine brückenfreie Lösung überhaupt existiert


def build_candidate(inst, seed):
    """Kandidatennetz für den Entwurf: das Netz selbst; hat es Brücken, kommt die Verstärkung (⌈L / 2⌉ Leitungen) dazu. Kosten je Leitung aus `edge_costs`."""
    adj = inst.adj
    added = () if A.is_two_edge_connected(adj) else A.augment(adj).edges
    pairs = tuple(sorted(set(inst.pairs) | set(added)))
    costs = S.edge_costs(S.Instance(inst.n, pairs, inst.xy, inst.kind), seed)
    return Candidate(pairs, costs, added)


@dataclass(frozen=True)
class Analysis:
    settings: Settings
    inst: S.Instance = field(compare=False, repr=False)
    aug: A.Augmentation = field(compare=False, repr=False)
    cand: Candidate = field(compare=False, repr=False)
    mst: tuple = field(compare=False, repr=False)                        # Indizes der Leitungen des billigsten Spannbaums
    lp: A.CoverSolution = field(compare=False, repr=False)
    exact: A.CoverSolution | None = field(compare=False, repr=False)     # nur bei höchstens BRUTE_N Standorten
    rounding: A.Rounding = field(compare=False, repr=False)
    critical_net: tuple | None = field(compare=False, repr=False)        # kritische Paare des Netzes (None bei Brücken)
    critical_cand: tuple = field(compare=False, repr=False)              # des ganzen Kandidatennetzes
    critical_design: tuple = field(compare=False, repr=False)            # des Entwurfs (Optimum, sonst Ergebnis des Rundens)

    @property
    def n(self):
        return self.inst.n

    @property
    def m(self):
        return self.inst.m

    @property
    def mst_cost(self):
        return sum(self.cand.costs[i] for i in self.mst)

    @property
    def design(self):
        """Indizes der Leitungen des besten bekannten Entwurfs: Optimum, sonst Ergebnis des iterativen Rundens."""
        return A.chosen_edges(self.exact) if self.exact else self.rounding.chosen

    @property
    def design_cost(self):
        return int(round(self.exact.value)) if self.exact else self.rounding.cost

    @property
    def optimum(self):
        return int(round(self.exact.value)) if self.exact else None

    @property
    def lp_value(self):
        return self.lp.value

    @property
    def rounding_ratio(self):
        return self.rounding.cost / self.optimum if self.exact else None

    @property
    def bridges(self):
        return self.aug.tree.bridges

    @property
    def cand_adj(self):
        return A.adj_from_edges(self.n, self.cand.pairs)

    @property
    def design_adj(self):
        return A.adj_from_edges(self.n, [self.cand.pairs[i] for i in self.design])


def analyse(settings: Settings) -> Analysis:
    inst = S.make_instance(settings.kind, settings.n, settings.deg, settings.links, settings.seed)
    adj = inst.adj
    aug = A.augment(adj)
    cand = build_candidate(inst, settings.seed)
    n, edges, costs = inst.n, cand.pairs, cand.costs
    mst = A.spanning_tree(n, edges, costs)
    lp = A.solve_cover(n, edges, costs)
    exact = A.solve_cover(n, edges, costs, integer=True) if n <= C.BRUTE_N else None
    rounding = A.iterative_rounding(n, edges, costs)
    critical_net = A.critical_pairs(adj) if not aug.tree.bridges else None
    critical_cand = A.critical_pairs(A.adj_from_edges(n, edges))
    design = A.chosen_edges(exact) if exact else rounding.chosen
    critical_design = A.critical_pairs(A.adj_from_edges(n, [edges[i] for i in design]))
    return Analysis(settings, inst, aug, cand, mst, lp, exact, rounding, critical_net, critical_cand, critical_design)


def within_factor_two(cost, lp_value):
    """Garantie des iterativen Rundens: Kosten ≤ 2 · Wert des linearen Programms (mit Toleranz)."""
    return cost <= 2 * lp_value + 1e-6


def validate(a: Analysis) -> list:
    """Unabhängige Prüfung vor der Anzeige: gibt die Liste der Probleme zurück (leer = alles in Ordnung)."""
    problems = []
    adj = a.inst.adj
    aug = a.aug
    existing = set(A.edges_of(adj))
    if aug.tree.bridges:
        if not A.is_two_edge_connected(A.add_edges(adj, aug.edges)):
            problems.append("Nach den neuen Leitungen hat das Netz noch eine Brücke")
        if len(aug.edges) != aug.lower_bound or len(aug.edges) != -(-len(aug.tree.leaves) // 2):
            problems.append("Die Zahl der neuen Leitungen ist nicht ⌈L / 2⌉")
        if any(e in existing or e[0] == e[1] for e in aug.edges):
            problems.append("Eine neue Leitung gibt es schon oder sie verbindet einen Standort mit sich selbst")
    elif aug.edges:
        problems.append("Das Netz hat keine Brücke, aber die Verstärkung nennt neue Leitungen")
    cand = a.cand
    if not A.is_two_edge_connected(A.adj_from_edges(a.n, cand.pairs)):
        problems.append("Das Kandidatennetz ist nicht 2-Kanten-zusammenhängend")
        return problems                                  # die Lösungen beziehen sich auf die Kandidaten: ohne gültiges Kandidatennetz lässt sich nichts weiter prüfen
    if len(a.mst) != a.n - 1 or not A.is_connected(A.adj_from_edges(a.n, [cand.pairs[i] for i in a.mst])):
        problems.append("Der Spannbaum ist keiner")
    lp = a.lp
    if any(v < -C.TOL or v > 1 + C.TOL for v in lp.x):
        problems.append("Das lineare Programm hat einen Wert außerhalb von [0, 1]")
    value, _side = A.min_cut_weighted(A._weights(a.n, cand.pairs, lp.x))
    if value < 2 - 1e-6:
        problems.append("Die Lösung des linearen Programms hat einen Schnitt unter 2")
    if a.exact is not None:
        ex = a.exact
        if not A.is_two_edge_connected(a.design_adj):
            problems.append("Das Optimum ist nicht 2-Kanten-zusammenhängend")
        if abs(sum(cand.costs[i] for i in A.chosen_edges(ex)) - ex.value) > 1e-6:
            problems.append("Die Kosten des Optimums stimmen nicht mit der Summe überein")
        if lp.value > ex.value + 1e-6:
            problems.append("Das lineare Programm ist teurer als das ganzzahlige")
        if ex.value < a.mst_cost - 1e-9:
            problems.append("Das Optimum ist billiger als ein Spannbaum")
        if a.rounding.cost < ex.value - 1e-6:
            problems.append("Das Runden liegt unter dem Optimum")
    rd = a.rounding
    if not A.is_two_edge_connected(A.adj_from_edges(a.n, [cand.pairs[i] for i in rd.chosen])):
        problems.append("Das Ergebnis des Rundens ist nicht 2-Kanten-zusammenhängend")
    if rd.cost != sum(cand.costs[i] for i in rd.chosen):
        problems.append("Die Kosten des Rundens stimmen nicht mit der Summe überein")
    if not within_factor_two(rd.cost, lp.value):
        problems.append("Das Runden liegt über dem Doppelten des linearen Programms")
    return problems


# --- Formate ---------------------------------------------------------------------------------------------------------------------------------------


def _i(x) -> str:
    """Ganze Zahl mit Punkt als Tausendertrenner."""
    return f"{x:,.0f}".replace(",", ".")


def _dec(x, digits=1) -> str:
    """Zahl mit Komma; ganze Werte ohne Nachkommastelle."""
    x = float(x)
    if x == int(x):
        return _i(x)
    return f"{x:,.{digits}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _r(x) -> str:
    """Verhältnis mit zwei Nachkommastellen."""
    return _dec(x, 2)


def _pct(share, digits=0) -> str:
    return _dec(round(100.0 * share, digits), digits) if digits else _i(round(100.0 * share))


def _share(share) -> str:
    """Anteil in Prozent: ganze Prozent, unter 10 % (aber nicht 0) mit einer Nachkommastelle, damit kleine Anteile nicht auf 0 runden."""
    return _pct(share) if share >= 0.1 else _pct(share, 1)


def _of(k, n) -> str:
    return f"{_i(k)} von {_i(n)}"


def _leitungen(c) -> str:
    return "1 Leitung" if c == 1 else f"{_i(c)} Leitungen"


def _bruecken(c) -> str:
    return "1 Brücke" if c == 1 else f"{_i(c)} Brücken"


def _blaetter(c) -> str:
    return "1 Blatt" if c == 1 else f"{_i(c)} Blätter"


# --- Verdikte -------------------------------------------------------------------------------------------------------------------------------------


def verdict_augment(a: Analysis):
    """Verstärken: Brücken, Blätter des Brückenbaums, neue Leitungen und der Stolperstein Vertreterwahl."""
    aug = a.aug
    if not aug.tree.bridges:
        return "info", f"**Das Netz hat keine Brücke:** Es ist schon 2-Kanten-zusammenhängend ({_i(a.n)} Standorte, {_i(a.m)} Leitungen); nichts zu verstärken."
    L = len(aug.tree.leaves)
    text = (f"**Das Netz hat {_bruecken(len(aug.tree.bridges))}**, der Brückenbaum hat {_i(len(aug.tree.blobs))} Komponenten und {_blaetter(L)}. Jede neue Leitung versorgt höchstens zwei Blätter, also braucht man mindestens "
            f"⌈{_i(L)} / 2⌉ = {_i(aug.lower_bound)} neue {'Leitung' if aug.lower_bound == 1 else 'Leitungen'}; die Paarung nach Tiefensuche benutzt {_i(len(aug.edges))}, danach ist das Netz brückenfrei.")
    if aug.naive_parallel:
        text += f" Mit dem kleinsten Standort als Vertreter wäre {'eine neue Leitung' if aug.naive_parallel == 1 else _i(aug.naive_parallel) + ' neue Leitungen'} parallel zu einer vorhandenen."
    return "info", text


def verdict_design(a: Analysis):
    """Entwerfen: Spannbaum, Programm, Optimum und iteratives Runden."""
    head = f"**Der billigste Spannbaum kostet {_i(a.mst_cost)}.**"
    if a.exact:
        opt = a.optimum
        extra = (opt - a.mst_cost) / a.mst_cost if a.mst_cost else 0.0
        body = f" Das Optimum (2-Kanten-zusammenhängend) kostet {_i(opt)}, also {_pct(extra)} % mehr; das lineare Programm {_dec(a.lp_value, 2)} (Lücke {_r(opt / a.lp_value)})."
        body += (f" Iteratives Runden braucht {_i(a.rounding.cost)} ({'das Optimum' if a.rounding.cost == opt else 'das ' + _r(a.rounding.cost / opt) + '-Fache'}; Garantie 2) in {_i(len(a.rounding.steps))} Schritten.")
    else:
        hit = a.rounding.cost <= a.lp_value + 1e-6
        body = (f" Über {_i(C.BRUTE_N)} Standorten gibt es keine exakte Lösung: Das lineare Programm kostet {_dec(a.lp_value, 2)} (untere Schranke); iteratives Runden braucht {_i(a.rounding.cost)}, "
                + ("genau die Schranke und damit das Optimum" if hit else f"höchstens das {_r(a.rounding.cost / a.lp_value)}-Fache der Schranke (Garantie 2)") + f", in {_i(len(a.rounding.steps))} Schritten.")
    if a.lp.integral:
        body += " Die Lösung des Programms ist ganzzahlig."
    return "info", head + body


def verdict_double(a: Analysis):
    """Doppelausfälle: kritische Kantenpaare im Kandidatennetz und im Entwurf."""
    mc, md = len(a.cand.pairs), len(a.design)
    pc, pd = len(a.critical_cand), len(a.critical_design)
    sc = pc / A.comb2(mc) if A.comb2(mc) else 0.0
    sd = pd / A.comb2(md) if A.comb2(md) else 0.0
    text = (f"**Im Entwurf mit {_leitungen(md)} trennen {_of(pd, A.comb2(md))} Leitungspaaren ({_share(sd)} %) das Netz**, im ganzen Kandidatennetz mit {_leitungen(mc)} "
            f"{_of(pc, A.comb2(mc))} ({_share(sc)} %).")
    return "info", text


def verdict_augment_rows(rows):
    nets = sum(r["nets"] for r in rows)
    with_b = sum(r["with_bridges"] for r in rows)
    ok = sum(r["ok"] for r in rows)
    sum_b, sum_l, sum_new = (sum(r[k] for r in rows) for k in ("sum_bridges", "sum_leaves", "sum_new"))
    naive = sum(r["naive_nets"] for r in rows)
    if ok != with_b:
        return "warning", f"Bei {_of(with_b - ok, with_b)} Netzen mit Brücken ist die Verstärkung nicht brückenfrei oder nicht ⌈L / 2⌉."
    text = (f"Von {_i(nets)} Netzen ({len(rows)} Netztypen, {_i(rows[0]['n'])} Standorte, mittlerer Grad {_dec(C.EX_AUG_DEG)}) haben {_i(with_b)} Brücken ({_i(sum_b)} insgesamt, im Mittel {_dec(sum_b / with_b)} je Netz mit Brücken); "
            f"die Blätter der Brückenbäume ({_i(sum_l)}) brauchen {_i(sum_new)} neue Leitungen, in allen {_i(with_b)} Netzen genau ⌈L / 2⌉ und brückenfrei danach.")
    text += f" Mit dem kleinsten Standort als Vertreter wäre in {_of(naive, with_b)} Netzen eine neue Leitung parallel zu einer vorhandenen." if naive else " Auch mit dem kleinsten Standort als Vertreter entstand nirgends eine parallele Leitung."
    return "info", text


def verdict_design_rows(rows):
    nets = sum(r["nets"] for r in rows)
    mst, opt, lp, rd = (sum(r[k] for r in rows) for k in ("sum_mst", "sum_opt", "sum_lp", "sum_round"))
    gap = max(r["max_gap"] for r in rows)
    worst = max(rows, key=lambda r: r["max_round"])
    hit = sum(r["round_exact"] for r in rows)
    integral = sum(r["lp_integral"] for r in rows)
    ratios = [r["sum_opt"] / r["sum_mst"] for r in rows]
    text = (f"Auf {_i(nets)} Netzen mit {_i(rows[0]['n'])} Standorten kostet das Optimum im Mittel (Quotient der Summen) das {_r(opt / mst)}-Fache des billigsten Spannbaums (je Netztyp {_r(min(ratios))} bis {_r(max(ratios))}). "
            f"Die Lücke zum linearen Programm ist höchstens {_r(gap)} (Summe der Kosten {_i(opt)} gegen {_dec(lp, 1)}), seine Lösung ist in {_of(integral, nets)} Netzen ganzzahlig. Iteratives Runden trifft das Optimum in "
            f"{_of(hit, nets)} Netzen, kostet im Mittel das {_r(rd / opt)}-Fache und im schlechtesten Netz das {_r(worst['max_round'])}-Fache ({worst['label']}; Garantie 2).")
    return "info", text


def verdict_cuts_rows(rows):
    nets = sum(r["nets"] for r in rows)
    cuts = sum(r["sum_cuts"] for r in rows)
    worst = max(r["max_cuts"] for r in rows)
    total = rows[0]["total_cuts"]
    rounds = sum(r["sum_rounds"] for r in rows)
    return "info", (f"Von {_i(total)} möglichen Schnittbedingungen (bei {_i(rows[0]['n'])} Standorten) lädt das Verfahren im Mittel {_dec(cuts / nets)} {'Schnitt' if cuts == nets else 'Schnitte'} nach (höchstens {_i(worst)}) und löst das "
                    f"Programm im Mittel {_dec(rounds / nets)}-mal; die {_i(rows[0]['n'])} Gradbedingungen stehen von Anfang an dabei.")


def verdict_double_rows(rows):
    nets = sum(r["nets"] for r in rows)
    pc, ac = sum(r["sum_pairs_cand"] for r in rows), sum(r["sum_all_cand"] for r in rows)
    pd, ad = sum(r["sum_pairs_design"] for r in rows), sum(r["sum_all_design"] for r in rows)
    cyc = sum(r["design_cycle"] for r in rows)
    return "info", (f"Im ganzen Kandidatennetz trennen {_share(pc / ac)} % aller Leitungspaare das Netz, im billigsten Entwurf {_share(pd / ad)} % (über {_i(nets)} Netze): Der Entwurf hat weniger Leitungen und ist verwundbarer; ob die Kostenminimierung die Ursache ist, misst der Vergleich nicht. "
                    f"In {_of(cyc, nets)} Netzen ist der Entwurf ein einziger Kreis über alle Standorte (dann trennt jedes Paar).")

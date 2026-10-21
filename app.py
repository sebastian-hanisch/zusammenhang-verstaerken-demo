"""Zusammenhang verstärken und Netze entwerfen - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Viertes Stück der Reihe „Schnitte und Zusammenhang“ (gebaut als fünftes): Welche Leitungen fehlen, damit kein einzelner Ausfall das Netz trennt, und was kostet das? Brückenbaum und Blattpaarung, billigstes
2-Kanten-zusammenhängendes Teilnetz (lineares Programm mit nachgeladenen Schnittbedingungen, iteratives Runden, exakte Lösung) und kritische Leitungspaare bei Doppelausfällen.

Lauffähig mit: streamlit run app.py
"""

import pandas as pd
import streamlit as st

import zvs_algorithm as A
import zvs_constants as C
import zvs_evaluation as ev
import zvs_experiments as ex
from zvs_layout import dunkles_design, kopf_css
from zvs_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from zvs_visualization import (
    build_augment,
    build_bridge_map,
    build_cuts,
    build_design,
    build_design_map,
    build_double,
    build_pair_map,
)

st.set_page_config(page_title="Zusammenhang verstärken und Netze entwerfen – Sebastian Hanisch", layout="wide")

_i, _dec, _r = ev._i, ev._dec, ev._r


def _show(verdict):
    kind, text = verdict
    {"success": st.success, "info": st.info, "warning": st.warning}[kind](text)


@st.cache_data(show_spinner=False, max_entries=8)
def _analysis(settings):
    return ev.analyse(settings)


@st.cache_data(show_spinner=False)
def _augment():
    return ex.augment_rows()


@st.cache_data(show_spinner=False)
def _design():
    return ex.design_rows()


@st.cache_data(show_spinner=False)
def _cuts():
    return ex.cuts_rows()


@st.cache_data(show_spinner=False)
def _double():
    return ex.double_rows()


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in zvs_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🌉 Zusammenhang verstärken und Netze entwerfen")
st.markdown(
    """
**Welche Leitungen fehlen, damit kein einzelner Ausfall das Netz trennt, und was kostet das?** Eine **Brücke** ist eine Leitung, deren Ausfall das Netz in zwei Teile zerlegt. Ein Netz ohne Brücke heißt
**2-Kanten-zusammenhängend**. Die Demo zeigt zwei Aufgaben: **Verstärken** (ein vorhandenes Netz mit möglichst wenigen neuen Leitungen brückenfrei machen: zieht man die brückenfreien Teile zu Punkten zusammen, entsteht ein Baum,
und man verbindet seine **Blätter** paarweise) und **Entwerfen** (aus Kandidatenleitungen mit Kosten die billigste Auswahl treffen, die brückenfrei verbindet; NP-schwer). Für das Entwerfen rechnet die Demo ein **lineares Programm**
mit **nachgeladenen Schnittbedingungen**, **rundet iterativ** (Garantie 2) und vergleicht mit der **exakten** Lösung.

Auffällig: Das Verstärken ist **einfach** (⌈L/2⌉ neue Leitungen bei L Blättern, aber die Wahl der Vertreter ist heikel); beim Entwerfen ist das **lineare Programm fast ganzzahlig**; und das billigste Teilnetz ist **verwundbarer** als das Kandidatennetz:
Es ist oft ein einziger Kreis, in dem **jedes** Paar von Leitungen das Netz trennt (Tab Doppelausfälle).

Das ist das vierte Stück der Reihe **Schnitte und Zusammenhang**; Brücken zählt **bridges-demo**, Zusammenhang über disjunkte Wege zeigt **menger-demo**, Schnittbedingungen für **Flusskapazitäten** nachzuladen zeigt **fixkosten-netzdesign-demo**.
Weiter unten: die Experimente **🔬**, **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So verstärkt und entwirft man", expanded=True):
    st.markdown(
        """
1. **Brückenbaum:** Man entfernt alle Brücken und erhält die **2-Kanten-Zusammenhangskomponenten**; zieht man jede zu einem Punkt zusammen und setzt die Brücken wieder ein, ist das Ergebnis ein **Baum**. Seine **Blätter** sind die Komponenten mit nur einer Brücke.
2. **Verstärken:** Jede neue Leitung sichert höchstens zwei Blätter, also braucht man mindestens ⌈L / 2⌉ neue Leitungen. Sortiert man die Blätter in Tiefensuch-Reihenfolge und verbindet Blatt i mit Blatt i + ⌊L / 2⌋, reicht das auch aus.
3. **Vertreter:** Die neue Leitung setzt in einem Blatt an einem Standort an; er darf **nicht der Endpunkt der Brücke** sein, sonst kann die neue Leitung zu einer vorhandenen parallel laufen.
4. **Entwerfen:** Aus den Kandidatenleitungen mit Kosten wählt man eine billigste Menge, bei der jeder Schnitt mindestens zwei Leitungen hat. **Lineares Programm:** Jede Leitung bekommt einen Wert zwischen 0 und 1; es gibt 2^(n−1) − 1 Schnittbedingungen, die nach und nach **nachgeladen** werden (der kleinste Schnitt der Lösung per Stoer–Wagner).
5. **Iteratives Runden:** Man setzt eine Leitung mit Wert mindestens ½ auf 1 und rechnet mit den übrigen weiter; die Kosten sind höchstens doppelt so hoch wie die des Programms.

| Begriff | Bedeutung |
|---|---|
| **Brücke** | Leitung, deren Ausfall das Netz trennt |
| **Brückenbaum / Blatt** | die zusammengezogenen brückenfreien Teile, verbunden durch die Brücken; Blatt: Teil mit nur einer Brücke |
| **2-Kanten-zusammenhängend** | zusammenhängend und ohne Brücke: kein einzelner Leitungsausfall trennt das Netz |
| **Kandidatenleitungen** | die möglichen Trassen mit Kosten (hier: die Leitungen des Netzes, ergänzt um die Verstärkung, falls das Netz Brücken hat) |
| **Lineares Programm** | wie das Entwurfsproblem, aber mit Werten zwischen 0 und 1: eine untere Schranke für die Kosten |
| **Kritisches Paar** | zwei Leitungen, deren gemeinsamer Ausfall das Netz trennt, obwohl keine allein eine Brücke ist |
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Netz**")
    kind = st.selectbox("Art des Netzes", list(C.KINDS), format_func=C.KIND_NAMES.get, key="kind_select", help=C.KIND_HELP.get(st.session_state.get("kind_select", C.DEFAULT_KIND), ""))
    n = st.slider("Standorte n", *bounds("n_slider"), key="n_slider", help=f"Wie viele Standorte das Netz hat (das Gitter rundet auf ein Rechteck). Die exakte Lösung des Entwurfs läuft bis {C.BRUTE_N} Standorte.")
    deg = st.slider("Mittlerer Grad", *bounds("deg_slider"), key="deg_slider", step=0.5, help="Leitungen je Standort im Mittel; wirkt beim Zufallsnetz und innerhalb der Regionen des Verbundnetzes. Kleiner Grad: viele Brücken.")
    links = st.slider("Leitungen zwischen je zwei Regionen", *bounds("links_slider"), key="links_slider", help="Wirkt nur beim Verbundnetz.")
    seed = st.number_input("Zufalls-Seed", *bounds("seed_input"), key="seed_input", step=1, help="Legt das Netz und die Kosten der Leitungen fest.")
    st.button("🎲 Neues Netz erzeugen", width="stretch", on_click=randomize_seed)
    st.caption(C.KIND_REGLER[kind])

sync_query_params({"kind_select": kind, "n_slider": int(n), "deg_slider": float(deg), "links_slider": int(links), "seed_input": int(seed)})

settings = ev.Settings(kind, int(n), float(deg), int(links), int(seed))
with st.spinner("Rechne Brücken, das lineare Programm und das Runden..."):
    a = _analysis(settings)
problems = ev.validate(a)
for p in problems:
    st.error(f"Prüfung fehlgeschlagen: {p}")
signature = f"{settings.kind}_{settings.n}_{settings.deg}_{settings.links}_{settings.seed}"
inst = a.inst
cand = a.cand
aug = a.aug

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis")
st.caption(f"{C.KIND_NAMES[kind]} mit {_i(a.n)} Standorten und {_i(a.m)} Leitungen; Kosten je Leitung 1 bis {C.COST_MAX}. Standorte sind ab 1 nummeriert.")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Brücken", _i(len(a.bridges)), delta=(f"{_i(len(aug.tree.leaves))} Blätter, {_i(aug.lower_bound)} neue Leitungen" if a.bridges else "brückenfrei"), delta_color="off")
m2.metric("Billigster Spannbaum", _i(a.mst_cost), delta=f"{_i(a.n - 1)} Leitungen", delta_color="off")
if a.exact:
    m3.metric("Optimum (2-kantenzusammenhängend)", _i(a.optimum), delta=f"{_dec(100 * (a.optimum - a.mst_cost) / a.mst_cost, 0)} % über dem Spannbaum", delta_color="off")
    m4.metric("Iteratives Runden", _i(a.rounding.cost), delta="trifft das Optimum" if a.rounding.cost == a.optimum else f"{_r(a.rounding.cost / a.optimum)}-fach", delta_color="off" if a.rounding.cost == a.optimum else "inverse")
else:
    m3.metric("Lineares Programm", _dec(a.lp_value, 1), delta=f"untere Schranke (über {C.BRUTE_N} Standorte keine exakte Lösung)", delta_color="off")
    m4.metric("Iteratives Runden", _i(a.rounding.cost), delta="trifft die Schranke (optimal)" if a.rounding.cost <= a.lp_value + 1e-6 else f"höchstens {_r(a.rounding.cost / a.lp_value)}-fach", delta_color="off")
_show(ev.verdict_design(a))

tab_aug, tab_design, tab_double = st.tabs(["🌉 Verstärken", "📐 Entwerfen", "💥 Doppelausfälle"])

# --- Tab 1: Verstärken ---------------------------------------------------------------------------------------------------------------------

with tab_aug:
    rep_mode = st.radio("Vertreter der Blätter", ["nicht der Endpunkt der Brücke", "kleinster Standort (naiv)"], horizontal=True, key=f"rep_{signature}",
                        help="Wo die neue Leitung im Blatt ansetzt. Der kleinste Standort kann der Endpunkt der Brücke sein.")
    naive = rep_mode.startswith("kleinster")
    new_edges = aug.naive_edges if naive else aug.edges
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Das Netz: Brücken und Brückenbaum**")
        st.plotly_chart(build_bridge_map(inst, aug.tree, (), height=420), width="stretch", key=f"bridge_map_{signature}")
        st.caption("Farbe: 2-Kanten-Zusammenhangskomponente (Rauten: Blätter des Brückenbaums); rot: die Brücken.")
    with c2:
        st.markdown(f"**Mit {_i(len(new_edges))} neuen Leitungen**" if a.bridges else "**Nichts zu verstärken**")
        st.plotly_chart(build_bridge_map(inst, aug.tree, new_edges, height=420), width="stretch", key=f"aug_map_{signature}_{int(naive)}")
        st.caption("Grün gestrichelt: die neuen Leitungen, jeweils zwischen zwei Blättern." if a.bridges else "Das Netz hat keine Brücke.")
    if a.bridges:
        rows = []
        for idx, (p, q) in enumerate(aug.pairs):
            u, v = sorted((A.representative(aug.tree, p, naive), A.representative(aug.tree, q, naive)))
            rows.append({"Blatt": f"{_i(aug.tree.leaves.index(p) + 1)} und {_i(aug.tree.leaves.index(q) + 1)}", "Standorte im Blatt": f"{', '.join(inst.name(x) for x in aug.tree.blobs[p])} | {', '.join(inst.name(x) for x in aug.tree.blobs[q])}",
                         "Neue Leitung": f"{inst.name(u)} – {inst.name(v)}"})
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        st.caption(f"Die Blätter {', '.join(_i(i + 1) for i in range(len(aug.tree.leaves)))} stehen in Tiefensuch-Reihenfolge; Blatt i wird mit Blatt i + ⌊L / 2⌋ verbunden (L = {_i(len(aug.tree.leaves))}).")
        if naive and aug.naive_parallel:
            st.warning(f"Mit dem kleinsten Standort als Vertreter läuft {'eine neue Leitung' if aug.naive_parallel == 1 else _i(aug.naive_parallel) + ' neue Leitungen'} **parallel zu einer vorhandenen** (hier zur Brücke): "
                       f"Das Netz hätte danach dieselbe Leitung doppelt und wäre nicht verstärkt.")
        elif not A.is_two_edge_connected(A.add_edges(inst.adj, new_edges)):
            st.warning("Mit diesen Vertretern bleibt eine Brücke übrig.")
    _show(ev.verdict_augment(a))

# --- Tab 2: Entwerfen ---------------------------------------------------------------------------------------------------------------------

with tab_design:
    views = ["Kandidatennetz mit Kosten", "Billigster Spannbaum", "Lineares Programm", "Iteratives Runden"] + (["Optimum (exakt)"] if a.exact else [])
    view = st.selectbox("Ansicht", views, key=f"view_{signature}", help="Welche Lösung auf der Karte gezeigt wird. Zahlen an den Leitungen: ihre Kosten (bis 20 Standorte).")
    d1, d2 = st.columns([3, 2])
    with d1:
        kw = dict(pairs=cand.pairs, costs=cand.costs, added=cand.added)
        if view.startswith("Kandidaten"):
            fig = build_design_map(inst, **kw, height=440)
        elif view.startswith("Billigster"):
            fig = build_design_map(inst, **kw, mst=a.mst, height=440)
        elif view.startswith("Lineares"):
            fig = build_design_map(inst, **kw, x=a.lp.x, height=440)
        elif view.startswith("Iteratives"):
            fig = build_design_map(inst, **kw, chosen=a.rounding.chosen, height=440)
        else:
            fig = build_design_map(inst, **kw, chosen=A.chosen_edges(a.exact), height=440)
        st.plotly_chart(fig, width="stretch", key=f"design_map_{signature}_{views.index(view)}")
        st.caption("Grau: Kandidatenleitungen; grün: gewählt; blau: Spannbaum; im linearen Programm ist die Breite der Wert, gelb sind gebrochene Werte; grün gepunktet: Leitungen, die die Verstärkung ergänzt hat, damit eine brückenfreie Lösung existiert.")
    with d2:
        rows = [{"Lösung": "Spannbaum", "Leitungen": _i(a.n - 1), "Kosten": _i(a.mst_cost)}, {"Lösung": "Lineares Programm", "Leitungen": "-", "Kosten": _dec(a.lp_value, 2)}]
        if a.exact:
            rows.append({"Lösung": "Optimum (exakt)", "Leitungen": _i(len(A.chosen_edges(a.exact))), "Kosten": _i(a.optimum)})
        rows.append({"Lösung": "Iteratives Runden", "Leitungen": _i(len(a.rounding.chosen)), "Kosten": _i(a.rounding.cost)})
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        st.caption(f"{_i(len(cand.pairs))} Kandidatenleitungen, davon {_i(len(cand.added))} von der Verstärkung ergänzt. Das lineare Programm ist {'ganzzahlig' if a.lp.integral else 'gebrochen'}; es löste {_i(a.lp.rounds)}-mal, "
                   f"mit {_i(len(a.lp.cuts))} nachgeladenen Schnitten (von {_i(2 ** (a.n - 1) - 1) if a.n <= 30 else '2^' + str(a.n - 1)} möglichen).")
        if a.lp.cuts:
            cut_rows = [{"Nr.": _i(k + 1), "Seite des Schnitts": ", ".join(inst.name(v) for v in side) if len(side) <= 8 else f"{_i(len(side))} Standorte"} for k, side in enumerate(a.lp.cuts)]
            st.markdown("**Nachgeladene Schnitte**")
            st.dataframe(pd.DataFrame(cut_rows), hide_index=True, width="stretch")
    with st.expander("Schritte des iterativen Rundens"):
        steps = [{"Schritt": _i(k + 1), "Leitung": f"{inst.name(cand.pairs[s.edge][0])} – {inst.name(cand.pairs[s.edge][1])}", "Kosten": _i(cand.costs[s.edge]), "Wert im Programm": _dec(s.value, 2),
                  "Kosten des Programms davor": _dec(s.lp_value, 2)} for k, s in enumerate(a.rounding.steps)]
        st.dataframe(pd.DataFrame(steps), hide_index=True, width="stretch")
        st.caption("In jedem Schritt wird die Leitung mit dem größten Wert (mindestens ½, bei Gleichstand die kleinere Nummer) fest gewählt; die Kosten des Programms steigen von Schritt zu Schritt oder bleiben gleich.")
    _show(ev.verdict_design(a))

# --- Tab 3: Doppelausfälle ----------------------------------------------------------------------------------------------------------------

with tab_double:
    design_pairs = [cand.pairs[i] for i in a.design]
    which = st.selectbox("Entwurf oder Netz", ["billigster Entwurf", "ganzes Kandidatennetz"] + (["das Netz (ohne Brücken)"] if a.critical_net is not None else []), key=f"dbl_{signature}")
    if which.startswith("billigster"):
        shown_pairs, crit = design_pairs, a.critical_design
    elif which.startswith("ganzes"):
        shown_pairs, crit = list(cand.pairs), a.critical_cand
    else:
        shown_pairs, crit = list(inst.pairs), a.critical_net
    total = A.comb2(len(shown_pairs))
    t1, t2, t3 = st.columns(3)
    t1.metric("Leitungen", _i(len(shown_pairs)))
    t2.metric("Kritische Paare", _i(len(crit)), delta=f"von {_i(total)} Paaren", delta_color="off")
    t3.metric("Anteil", f"{_dec(100 * len(crit) / total, 1) if total else '0'} %")
    if crit:
        pair = st.selectbox("Kritisches Paar", list(range(min(len(crit), 200))), format_func=lambda k: f"{inst.name(crit[k][0][0])}–{inst.name(crit[k][0][1])} und {inst.name(crit[k][1][0])}–{inst.name(crit[k][1][1])}", key=f"pair_{signature}_{which}",
                            help="Fällt dieses Paar von Leitungen aus, zerfällt das Netz (bis zu 200 Paare zur Auswahl).")
        st.plotly_chart(build_pair_map(inst, shown_pairs, crit[int(pair)], height=420), width="stretch", key=f"pair_map_{signature}_{which}_{int(pair)}")
        st.caption("Rot gestrichelt: das ausgewählte Leitungspaar; ohne diese beiden Leitungen ist das Netz nicht mehr zusammenhängend.")
    else:
        st.success("Kein Leitungspaar trennt dieses Netz: Es ist 3-Kanten-zusammenhängend.")
    _show(ev.verdict_double(a))

st.markdown("---")

# --- Experimente ---------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🔬 Experimente über feste Netze")
st.caption(f"Je Netztyp feste Netze mit festen Zufalls-Seeds: {C.EX_AUG_SEEDS} Netze mit {C.EX_AUG_N} Standorten für das Verstärken, {len(C.SWEEP_SEEDS)} mit {C.EX_N} Standorten für den Entwurf; nie ein einzelner Zufalls-Seed als Befund.")

st.subheader("🔬 Experiment 1: Wie viele Leitungen braucht das Verstärken?")
rows_a = _augment()
st.caption(f"Netze mit {C.EX_AUG_N} Standorten und mittlerem Grad {_dec(C.EX_AUG_DEG)} (Zufalls- und Verbundnetz; die anderen Typen haben ihren eigenen Grad): Summe der Brücken, der Blätter des Brückenbaums und der neuen Leitungen.")
st.plotly_chart(build_augment(rows_a), width="stretch", key="ex_augment")
_show(ev.verdict_augment_rows(rows_a))

st.subheader("🔬 Experiment 2: Was kostet Redundanz, und wie gut ist das Runden?")
rows_d = _design()
st.caption(f"Kosten (Mittel über {len(C.SWEEP_SEEDS)} Netze je Typ, {C.EX_N} Standorte): Spannbaum, lineares Programm, Optimum und iteratives Runden.")
st.plotly_chart(build_design(rows_d), width="stretch", key="ex_design")
_show(ev.verdict_design_rows(rows_d))

st.subheader("🔬 Experiment 3: Wie viele Schnittbedingungen muss man nachladen?")
rows_c = _cuts()
st.caption(f"Nachgeladene Schnitte des linearen Programms (Mittel über {len(C.SWEEP_SEEDS)} Netze je Typ), gegen die Zahl aller Schnittbedingungen.")
st.plotly_chart(build_cuts(rows_c), width="stretch", key="ex_cuts")
_show(ev.verdict_cuts_rows(rows_c))

st.subheader("🔬 Experiment 4: Wie verwundbar ist der billigste Entwurf?")
rows_x = _double()
st.caption("Anteil der Leitungspaare, deren gemeinsamer Ausfall das Netz trennt: im ganzen Kandidatennetz und im billigsten Entwurf.")
st.plotly_chart(build_double(rows_x), width="stretch", key="ex_double")
_show(ev.verdict_double_rows(rows_x))

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Nur Leitungsausfälle** | Es zählen einzelne Leitungen; der Ausfall von Standorten (Knotenzusammenhang) ist ein anderes Maß. | menger-demo |
| **Zusammenhang 2, nicht höher** | Die Demo verstärkt auf 2-Kanten-Zusammenhang; höhere Ziele und gemischte Anforderungen je Paar (Steinernetz-Entwurf) sind nicht gebaut. | - |
| **Kosten je Leitung unabhängig** | Die Kosten sind ganze Zahlen von 1 bis 9, zufällig; echte Trassenkosten hängen von Länge, Gelände und Mitbenutzung ab. | fixkosten-netzdesign-demo |
| **Verstärken ohne Kosten** | Das Verstärken zählt neue Leitungen; mit Kosten je Kandidat wird es zum (NP-schweren) Entwurf mit vorhandenem Netz. | - |
| **Ein Ausfall, nicht zwei** | 2-Kanten-Zusammenhang schützt vor einem Ausfall; Doppelausfälle trennen den billigsten Entwurf oft (Tab Doppelausfälle). | - |
| **Synthetische Netze, bis 40 Standorte** | Die exakte Lösung läuft bis 14 Standorte, das lineare Programm und das Runden bis 40; reale Netze haben andere Strukturen. | - |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Gegeben** ein ungerichteter Graph $G = (V, E)$ mit $n = |V|$ Standorten. Eine Kante $e$ ist eine **Brücke**, wenn $G - e$ mehr Komponenten hat als $G$; $G$ ist **2-kantenzusammenhängend**, wenn es zusammenhängend und brückenfrei ist, gleichwertig $|\delta(S)| \ge 2$ für jede Menge $\emptyset \ne S \subsetneq V$.

**Verstärken.** Der Brückenbaum $T$ entsteht, indem man die 2-kantenzusammenhängenden Komponenten zu Punkten zusammenzieht. Hat $T$ genau $L$ Blätter, so sind mindestens

$$\left\lceil \frac{L}{2} \right\rceil$$

neue Kanten nötig, denn jedes Blatt von $T$ braucht eine neue Kante an sich, und eine neue Kante berührt höchstens zwei Blätter. Ordnet man die Blätter $\ell_1, \dots, \ell_L$ in Tiefensuch-Reihenfolge und fügt die Kanten $\{\ell_i, \ell_{i + \lfloor L/2 \rfloor}\}$ für $i = 1, \dots, \lceil L/2 \rceil$ ein, ist das Ergebnis 2-kantenzusammenhängend (Eswaran, Tarjan 1976); jede neue Kante setzt an einem Standort des Blatts an, der nicht Endpunkt der Brücke ist.

**Entwerfen.** Gegeben Kandidatenkanten $E$ mit Kosten $c_e \ge 0$. Gesucht ist $F \subseteq E$ mit $|F \cap \delta(S)| \ge 2$ für alle $S$ und kleinstem $c(F)$ (2-ECSS, NP-schwer). Lineares Programm:

$$\min \sum_{e \in E} c_e x_e \quad \text{mit} \quad x(\delta(S)) \ge 2 \;\; \forall\, \emptyset \ne S \subsetneq V, \qquad 0 \le x_e \le 1.$$

**Nachladen.** Man startet mit den Gradbedingungen $x(\delta(\{v\})) \ge 2$, löst, rechnet den kleinsten Schnitt von $G$ mit den Gewichten $x_e$ (Stoer–Wagner) und nimmt die Seite $S$ als neue Bedingung hinzu, wenn $x(\delta(S)) < 2$; sonst ist $x$ für alle Schnittbedingungen zulässig, denn der kleinste Schnitt ist mindestens 2.

**Iteratives Runden** (Jain). Man setzt $F = \emptyset$. In jedem Schritt löst man das Programm mit den Bedingungen $x(\delta(S)) \ge 2 - |F \cap \delta(S)|$ für die Kanten $E \setminus F$ in einer Ecke und nimmt eine Kante $e$ mit $x_e \ge \tfrac12$ in $F$ auf. Das gelingt in jedem Schritt (Jain), und es folgt

$$c(F) \;\le\; 2 \cdot \mathrm{LP}.$$

**Doppelausfälle.** Zwei Kanten $e, f$, die keine Brücken sind, heißen **kritisch**, wenn $f$ in $G - e$ eine Brücke ist; ihr gemeinsamer Ausfall trennt $G$. In einem Kreis über alle Standorte ist jedes Paar kritisch.

**Literatur.** K. P. Eswaran, R. E. Tarjan: *Augmentation problems*, SIAM Journal on Computing 5 (4), 1976, S. 653–665. K. Jain: *A factor 2 approximation algorithm for the generalized Steiner network problem*, Combinatorica 21 (1), 2001, S. 39–60.
M. Stoer, F. Wagner: *A simple min-cut algorithm*, Journal of the ACM 44 (4), 1997, S. 585–591. Die Demo löst die Programme mit `scipy.optimize.linprog` und `milp` (HiGHS); das lineare Programm rechnet mit leicht gestörten Kosten, damit die Ecke eindeutig ist.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)

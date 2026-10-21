"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import plotly.graph_objects as go

import zvs_constants as C

BLOB_COLORS = ("#2F6B65", "#4c78a8", "#e8a33d", "#8d6cab", "#3a8f5c", "#b5651d", "#5b8def", "#c06c84")


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=360):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.25), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def _lines(inst, pairs):
    xs, ys = [], []
    for u, v in pairs:
        xs += [float(inst.xy[u, 0]), float(inst.xy[v, 0]), None]
        ys += [float(inst.xy[u, 1]), float(inst.xy[v, 1]), None]
    return xs, ys


def _map_layout(fig, inst, height=470):
    xs, ys = inst.xy[:, 0], inst.xy[:, 1]
    pad = 0.25 * max(float(xs.max() - xs.min()), float(ys.max() - ys.min()), 1.0)
    fig.update_xaxes(visible=False, range=[float(xs.min()) - pad, float(xs.max()) + pad])
    fig.update_yaxes(visible=False, range=[float(ys.min()) - pad, float(ys.max()) + pad])
    return _base(fig, height)


def _line_trace(fig, inst, pairs, color, width, dash=None, name=None):
    pairs = list(pairs)
    if not pairs:
        return
    xs, ys = _lines(inst, pairs)
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=color, width=width, dash=dash), hoverinfo="skip", name=name, showlegend=name is not None))


def _node_trace(fig, inst, colors, size, symbols=None, line_color="white", line_width=1):
    show_text = inst.n <= 40
    fig.add_trace(go.Scatter(
        x=[float(inst.xy[v, 0]) for v in range(inst.n)], y=[float(inst.xy[v, 1]) for v in range(inst.n)], mode="markers+text" if show_text else "markers",
        marker=dict(size=size, color=colors, symbol=symbols or "circle", line=dict(color=line_color, width=line_width)), text=[inst.name(v) for v in range(inst.n)] if show_text else None,
        textfont=dict(size=10, color="#ffffff"), textposition="middle center", hovertext=[f"Standort {inst.name(v)}" for v in range(inst.n)], hoverinfo="text", showlegend=False))


def build_bridge_map(inst, tree, new=(), height=470):
    """Karte für das Verstärken: Standorte nach 2-Kanten-Zusammenhangskomponente gefärbt (Blätter als Rauten), Brücken rot, neue Leitungen grün gestrichelt."""
    br = set(tree.bridges)
    new = {(min(u, v), max(u, v)) for u, v in new}
    rest = [e for e in inst.pairs if e not in br and e not in new]
    fig = go.Figure()
    _line_trace(fig, inst, rest, C.COLOR_EDGE, 1.6)
    _line_trace(fig, inst, sorted(br), C.COLOR_BRIDGE, 3.4, name=f"Brücken ({len(br)})")
    _line_trace(fig, inst, sorted(new), C.COLOR_NEW, 3.2, dash="dot", name=f"neue Leitungen ({len(new)})")
    leaf_set = set(tree.leaves)
    colors = [BLOB_COLORS[tree.owner[v] % len(BLOB_COLORS)] for v in range(inst.n)]
    symbols = ["diamond" if tree.owner[v] in leaf_set else "circle" for v in range(inst.n)]
    _node_trace(fig, inst, colors, 22 if inst.n <= 40 else 11, symbols)
    return _map_layout(fig, inst, height)


def _cost_labels(fig, inst, pairs, costs, indices, color="#555555"):
    xs = [float((inst.xy[pairs[i][0], 0] + inst.xy[pairs[i][1], 0]) / 2) for i in indices]
    ys = [float((inst.xy[pairs[i][0], 1] + inst.xy[pairs[i][1], 1]) / 2) for i in indices]
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="text", text=[str(costs[i]) for i in indices], textfont=dict(size=11, color=color), hoverinfo="skip", showlegend=False))


def build_design_map(inst, pairs, costs, chosen=(), x=None, mst=(), added=(), height=470, labels=True):
    """Karte des Entwurfs: Kandidatenleitungen grau, gewählte grün; mit `x` (Wert je Leitung) wird die Breite zum Wert, gebrochene Werte gelb; `mst` zeichnet den Spannbaum blau; Kosten an den Leitungen."""
    chosen, mst, added = set(chosen), set(mst), {(min(u, v), max(u, v)) for u, v in added}
    fig = go.Figure()
    other = [pairs[i] for i in range(len(pairs)) if i not in chosen and i not in mst and (x is None or x[i] < C.TOL)]
    _line_trace(fig, inst, other, C.COLOR_EDGE, 1.1)
    if x is not None:
        for i, e in enumerate(pairs):
            if x[i] >= C.TOL:
                whole = x[i] > 1 - C.TOL
                _line_trace(fig, inst, [e], C.COLOR_CHOSEN if whole else C.COLOR_FRACTION, 1.5 + 3.5 * x[i])
    _line_trace(fig, inst, [pairs[i] for i in sorted(mst)], C.COLOR_BAR, 3.4)
    if x is None:
        _line_trace(fig, inst, [pairs[i] for i in sorted(chosen)], C.COLOR_CHOSEN, 3.6)
    _line_trace(fig, inst, sorted(added), C.COLOR_NEW, 1.6, dash="dot")
    if labels and inst.n <= 20:
        _cost_labels(fig, inst, pairs, costs, list(range(len(pairs))))
    _node_trace(fig, inst, [C.COLOR_SIDE_A] * inst.n, 20 if inst.n <= 40 else 10)
    return _map_layout(fig, inst, height)


def build_pair_map(inst, adj_pairs, critical_pair=None, height=420):
    """Karte der Doppelausfälle: das Netz grau, das gewählte kritische Paar rot gestrichelt."""
    fig = go.Figure()
    hot = {tuple(e) for e in (critical_pair or ())}
    _line_trace(fig, inst, [e for e in adj_pairs if e not in hot], C.COLOR_EDGE, 2.0)
    _line_trace(fig, inst, sorted(hot), C.COLOR_CUT, 3.8, dash="dot", name="ausgefallen")
    _node_trace(fig, inst, [C.COLOR_SIDE_B] * inst.n, 20 if inst.n <= 40 else 10)
    return _map_layout(fig, inst, height)


# --- Experimente ---------------------------------------------------------------------------------------------------------------------------------


def build_augment(rows):
    labels = [r["label"] for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=labels, y=[r["sum_bridges"] for r in rows], name="Brücken", marker_color=C.COLOR_BRIDGE, hovertemplate="%{x}: %{y}<extra></extra>"))
    fig.add_trace(go.Bar(x=labels, y=[r["sum_leaves"] for r in rows], name="Blätter des Brückenbaums", marker_color=C.COLOR_BAR, hovertemplate="%{x}: %{y}<extra></extra>"))
    fig.add_trace(go.Bar(x=labels, y=[r["sum_new"] for r in rows], name="neue Leitungen (⌈L / 2⌉)", marker_color=C.COLOR_BAR3, hovertemplate="%{x}: %{y}<extra></extra>"))
    fig.update_layout(barmode="group")
    fig.update_yaxes(title_text=f"Summe über je {C.EX_AUG_SEEDS} Netze", rangemode="tozero")
    return _base(fig, 380)


def build_design(rows):
    labels = [r["label"] for r in rows]
    fig = go.Figure()
    for key, name, color in (("sum_mst", "Spannbaum", "#8a9a9c"), ("sum_lp", "lineares Programm", C.COLOR_FRACTION), ("sum_opt", "Optimum", C.COLOR_BAR3), ("sum_round", "iteratives Runden", C.COLOR_BAR)):
        fig.add_trace(go.Bar(x=labels, y=[round(r[key] / r["nets"], 1) for r in rows], name=name, marker_color=color, hovertemplate="%{x}: %{y}<extra></extra>"))
    fig.update_layout(barmode="group")
    fig.update_yaxes(title_text="Kosten (Mittel über die Netze)", rangemode="tozero")
    return _base(fig, 400)


def build_cuts(rows):
    labels = [r["label"] for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=labels, y=[round(r["sum_cuts"] / r["nets"], 2) for r in rows], name="nachgeladene Schnitte (Mittel)", marker_color=C.COLOR_BAR3, hovertemplate="%{x}: %{y}<extra></extra>"))
    fig.add_trace(go.Scatter(x=labels, y=[r["max_cuts"] for r in rows], mode="markers", marker=dict(size=11, symbol="diamond", color=C.COLOR_CUT), name="höchstens", hovertemplate="%{x}: %{y}<extra></extra>"))
    fig.update_yaxes(title_text=f"Schnitte von {rows[0]['total_cuts']:,}".replace(",", "."), rangemode="tozero")
    return _base(fig)


def build_double(rows):
    labels = [r["label"] for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=labels, y=[round(100 * r["sum_pairs_cand"] / r["sum_all_cand"], 1) for r in rows], name="im ganzen Kandidatennetz", marker_color=C.COLOR_BAR, hovertemplate="%{x}: %{y} %<extra></extra>"))
    fig.add_trace(go.Bar(x=labels, y=[round(100 * r["sum_pairs_design"] / r["sum_all_design"], 1) for r in rows], name="im billigsten Entwurf", marker_color=C.COLOR_CUT, hovertemplate="%{x}: %{y} %<extra></extra>"))
    fig.update_layout(barmode="group")
    fig.update_yaxes(title_text="Leitungspaare, die das Netz trennen (%)", range=[0, 105])
    return _base(fig, 380)

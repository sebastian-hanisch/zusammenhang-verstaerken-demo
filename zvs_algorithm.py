"""Kern: Brücken, Brückenbaum, Verstärkung auf Zusammenhang 2, Netzentwurf (kleinste Kosten, 2-Kanten-zusammenhängend), lineares Programm mit nachgeladenen Schnittbedingungen, iteratives Runden und
kritische Kantenpaare.

**Verstärken:** Eine **Brücke** ist eine Leitung, deren Ausfall das Netz trennt. Zieht man die 2-Kanten-Zusammenhangskomponenten zu Punkten zusammen, entsteht der **Brückenbaum**; seine **Blätter** sind die Komponenten
mit nur einer Brücke. Jede neue Leitung kann höchstens zwei Blätter versorgen, also braucht man mindestens ⌈L / 2⌉ neue Leitungen bei L Blättern; die Blätter in Tiefensuch-Reihenfolge zu paaren (Blatt i mit Blatt
i + ⌊L / 2⌋) erreicht das (Eswaran, Tarjan 1976). Als Vertreter eines Blatts nimmt die Demo einen Standort, der nicht Endpunkt der Brücke ist, damit keine neue Leitung zu einer vorhandenen parallel läuft.

**Entwerfen:** Aus Kandidatenleitungen mit Kosten wählt man eine billigste Menge, die alle Standorte 2-Kanten-zusammenhängend verbindet (NP-schwer). Lineares Programm: x_e in [0, 1], je Schnitt S gilt x(δ(S)) ≥ 2.
Es gibt 2^(n−1) − 1 Schnittbedingungen; sie werden **nachgeladen**: Man löst mit den bisher bekannten, sucht den kleinsten Schnitt der Lösung (Stoer–Wagner mit den Werten x_e als Gewichten) und nimmt ihn dazu, wenn er
unter 2 liegt. **Iteratives Runden** (Jain 1998): Man löst das Programm, setzt eine Leitung mit x_e ≥ 1/2 auf 1 (sie gehört zum Netz) und wiederholt mit den verbleibenden Leitungen und den um die gewählten
verminderten Anforderungen; die Kosten sind höchstens doppelt so hoch wie die des Programms."""

import math
from collections import deque
from dataclasses import dataclass

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, linprog, milp

import zvs_constants as C


def edges_of(adj):
    return tuple((u, v) for u in range(len(adj)) for v in adj[u] if u < v)


def add_edges(adj, new):
    """Das Netz mit zusätzlichen Leitungen (Paare (u, v))."""
    nb = [set(a) for a in adj]
    for u, v in new:
        nb[u].add(v)
        nb[v].add(u)
    return tuple(tuple(sorted(s)) for s in nb)


def adj_from_edges(n, edges):
    nb = [set() for _ in range(n)]
    for u, v in edges:
        nb[u].add(v)
        nb[v].add(u)
    return tuple(tuple(sorted(s)) for s in nb)


def components_without(adj, removed=()):
    """Zusammenhangskomponenten (als Tupel aufsteigend, nach kleinstem Element sortiert) nach dem Entfernen der Leitungen `removed`."""
    n = len(adj)
    removed = set(removed)
    seen = [False] * n
    comps = []
    for s in range(n):
        if seen[s]:
            continue
        seen[s] = True
        comp, queue = [s], deque([s])
        while queue:
            u = queue.popleft()
            for v in adj[u]:
                if not seen[v] and (min(u, v), max(u, v)) not in removed:
                    seen[v] = True
                    comp.append(v)
                    queue.append(v)
        comps.append(tuple(sorted(comp)))
    return comps


def is_connected(adj, removed=()):
    return len(components_without(adj, removed)) == 1


# --- Brücken und Brückenbaum ----------------------------------------------------------------------------------------------------------------------


def bridges(adj, removed=()):
    """Alle Brücken (u, v), u < v, nach dem Entfernen der Leitungen `removed` (Tiefensuche mit Low-Werten, ohne Rekursion); in jeder Komponente."""
    n = len(adj)
    removed = set(removed)
    disc = [-1] * n
    low = [0] * n
    out = []
    t = 0
    for root in range(n):
        if disc[root] != -1:
            continue
        disc[root] = low[root] = t
        t += 1
        stack = [(root, -1, iter(adj[root]))]
        while stack:
            u, parent, it = stack[-1]
            advanced = False
            for v in it:
                if (min(u, v), max(u, v)) in removed or v == parent:
                    continue
                if disc[v] == -1:
                    disc[v] = low[v] = t
                    t += 1
                    stack.append((v, u, iter(adj[v])))
                    advanced = True
                    break
                low[u] = min(low[u], disc[v])
            if not advanced:
                stack.pop()
                if stack:
                    p = stack[-1][0]
                    low[p] = min(low[p], low[u])
                    if low[u] > disc[p]:
                        out.append((min(p, u), max(p, u)))
    return tuple(sorted(out))


def is_two_edge_connected(adj):
    """Zusammenhängend und ohne Brücke (Kantenzusammenhang mindestens 2)."""
    return is_connected(adj) and not bridges(adj)


@dataclass(frozen=True)
class BridgeTree:
    bridges: tuple          # alle Brücken (u, v)
    blobs: tuple            # 2-Kanten-Zusammenhangskomponenten (Tupel von Standorten), nach kleinstem Standort sortiert
    owner: tuple            # je Standort der Index seiner Komponente
    tree: tuple             # je Komponente die Nachbarn im Brückenbaum als aufsteigende Indizes
    leaves: tuple           # Blätter in Tiefensuch-Reihenfolge (Wurzel: die erste Komponente mit Grad ≥ 2, sonst bei nur zwei Komponenten die erste)


def bridge_tree(adj):
    br = bridges(adj)
    blobs = tuple(components_without(adj, br))
    owner = [0] * len(adj)
    for i, b in enumerate(blobs):
        for v in b:
            owner[v] = i
    nb = [set() for _ in blobs]
    for u, v in br:
        nb[owner[u]].add(owner[v])
        nb[owner[v]].add(owner[u])
    tree = tuple(tuple(sorted(s)) for s in nb)
    if len(blobs) < 2:
        return BridgeTree(br, blobs, tuple(owner), tree, ())
    root = next((i for i in range(len(blobs)) if len(tree[i]) >= 2), 0)
    leaves, seen, stack = [], {root}, [root]
    while stack:
        u = stack.pop()
        if len(tree[u]) == 1:
            leaves.append(u)
        for v in reversed(tree[u]):
            if v not in seen:
                seen.add(v)
                stack.append(v)
    return BridgeTree(br, blobs, tuple(owner), tree, tuple(leaves))


def representative(bt, blob, naive=False):
    """Standort eines Blatts, an dem eine neue Leitung ansetzt: nicht der Endpunkt der Brücke (wenn die Komponente größer ist); `naive`: der kleinste Standort (kann der Endpunkt sein)."""
    members = bt.blobs[blob]
    if naive or len(members) == 1:
        return members[0]
    ends = {v for b in bt.bridges for v in b if bt.owner[v] == blob}
    return next(v for v in members if v not in ends)


@dataclass(frozen=True)
class Augmentation:
    tree: BridgeTree
    pairs: tuple            # Paare von Blättern (Indizes in `tree.blobs`), die verbunden werden
    edges: tuple            # die neuen Leitungen (u, v) mit u < v
    lower_bound: int        # ⌈L / 2⌉
    naive_edges: tuple      # dieselbe Paarung mit dem kleinsten Standort als Vertreter
    naive_parallel: int     # davon neue Leitungen, die schon als Leitung vorhanden sind


def augment(adj):
    """Verstärkung auf Zusammenhang 2 mit ⌈L / 2⌉ neuen Leitungen (L Blätter des Brückenbaums): Blatt i mit Blatt i + ⌊L / 2⌋, i = 0 .. ⌈L / 2⌉ − 1."""
    bt = bridge_tree(adj)
    leaves = bt.leaves
    L = len(leaves)
    if L == 0:
        return Augmentation(bt, (), (), 0, (), 0)
    h = L // 2
    pairs = tuple((leaves[i], leaves[i + h]) for i in range(-(-L // 2)))
    edges = tuple(sorted(tuple(sorted((representative(bt, a), representative(bt, b)))) for a, b in pairs))
    naive = tuple(sorted(tuple(sorted((representative(bt, a, True), representative(bt, b, True)))) for a, b in pairs))
    existing = set(edges_of(adj))
    return Augmentation(bt, pairs, edges, -(-L // 2), naive, sum(1 for e in naive if e in existing or e[0] == e[1]))


# --- Kosten, Spannbaum ----------------------------------------------------------------------------------------------------------------------------


def spanning_tree(n, edges, costs):
    """Billigster Spannbaum (Kruskal; Gleichstand: kleinere Leitungsnummer): Indizes der Leitungen."""
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    chosen = []
    for i in sorted(range(len(edges)), key=lambda i: (costs[i], i)):
        a, b = find(edges[i][0]), find(edges[i][1])
        if a != b:
            parent[a] = b
            chosen.append(i)
    return tuple(sorted(chosen))


# --- Kleinster Schnitt mit Gewichten (Stoer–Wagner) -----------------------------------------------------------------------------------------------


def min_cut_weighted(w):
    """Kleinster Schnitt eines Netzes mit symmetrischer Gewichtsmatrix `w` (Liste von Listen mit Zahlen): (Wert, eine Seite als aufsteigendes Tupel). Nicht zusammenhängend: Wert 0."""
    n = len(w)
    w = [list(r) for r in w]
    members = {v: [v] for v in range(n)}
    active = list(range(n))
    best = None
    while len(active) > 1:
        key = {v: 0.0 for v in active}
        rest = list(active)
        order, bind = [], []
        while rest:
            pick = min(rest, key=lambda v: (-key[v], v))
            order.append(pick)
            bind.append(key[pick])
            rest.remove(pick)
            for v in rest:
                key[v] += w[pick][v]
        last, before = order[-1], order[-2]
        if best is None or bind[-1] < best[0] - 1e-12:
            best = (bind[-1], tuple(sorted(members[last])))
        for x in active:
            if x != last and x != before:
                w[before][x] += w[last][x]
                w[x][before] = w[before][x]
        members[before].extend(members[last])
        active.remove(last)
    return best


# --- Lineares Programm mit nachgeladenen Schnittbedingungen ---------------------------------------------------------------------------------------


@dataclass(frozen=True)
class CoverSolution:
    x: tuple                # Wert je Leitung (gewählte feste Leitungen: 1.0)
    value: float            # Kosten Σ c_e x_e über alle Leitungen
    cuts: tuple             # die nachgeladenen Schnitte (Seiten als Tupel), in der Reihenfolge des Nachladens
    rounds: int             # Zahl der Lösungen des Programms
    integral: bool          # sind alle Werte 0 oder 1?


def _weights(n, edges, x):
    w = [[0.0] * n for _ in range(n)]
    for (u, v), val in zip(edges, x):
        w[u][v] += val
        w[v][u] += val
    return w


def solve_cover(n, edges, costs, fixed=(), integer=False, max_rounds=400):
    """Kleinste Kosten, damit jeder Schnitt mindestens 2 Leitungen hat: Programm mit nachgeladenen Schnittbedingungen. `fixed`: Indizes schon gewählter Leitungen (Wert 1, Kosten gezählt); `integer`: ganzzahlig statt
    linear (exakte Lösung). Das lineare Programm rechnet mit leicht gestörten Kosten (`C.PERTURB`), damit die Ecke eindeutig ist; `value` zählt die echten Kosten."""
    m = len(edges)
    fixed = tuple(sorted(set(fixed)))
    fixed_set = set(fixed)
    free = [i for i in range(m) if i not in fixed_set]
    cost = np.array([costs[i] for i in free], dtype=float)
    pert = cost + C.PERTURB * (np.arange(len(free)) + 1) / max(len(free), 1)
    cuts = []
    seen = set()

    def row(side):
        s = set(side)
        crossing = [(u in s) != (v in s) for u, v in edges]
        fixed_cross = sum(1 for i in fixed if crossing[i])
        return [1.0 if crossing[i] else 0.0 for i in free], 2 - fixed_cross

    for v in range(n):                                  # Start: die Gradbedingungen
        cuts.append((v,))
        seen.add((v,))
    rounds = 0
    while True:
        rows, rhs = [], []
        for side in cuts:
            r, b = row(side)
            if b > 0:
                rows.append(r)
                rhs.append(b)
        rounds += 1
        if not free or not rows:                        # nichts zu entscheiden: alle freien Leitungen bleiben bei 0
            xs = np.zeros(len(free))
        else:
            A = np.array(rows, dtype=float)
            b = np.array(rhs, dtype=float)
            if integer:
                res = milp(cost, constraints=LinearConstraint(A, lb=b, ub=np.inf), integrality=np.ones(len(free)), bounds=Bounds(0, 1))
                ok, xs = res.success, res.x
            else:
                res = linprog(pert, A_ub=-A, b_ub=-b, bounds=(0, 1), method="highs-ds")
                ok, xs = res.status == 0, res.x
            if not ok:
                raise ValueError("kein 2-kantenzusammenhängendes Teilnetz aus den Kandidatenleitungen")
        x = [0.0] * m
        for i in fixed:
            x[i] = 1.0
        for j, i in enumerate(free):
            x[i] = float(xs[j])
        if integer:
            x = [float(round(v)) for v in x]
        value, side = min_cut_weighted(_weights(n, edges, x))
        if value >= 2 - C.TOL or side in seen or rounds >= max_rounds:
            break
        seen.add(side)
        cuts.append(side)
    total = sum(costs[i] * x[i] for i in range(m))
    return CoverSolution(tuple(x), float(total), tuple(cuts[n:]), rounds, all(abs(v - round(v)) < C.TOL for v in x))


def chosen_edges(solution):
    """Indizes der Leitungen mit Wert 1 (ganzzahlige Lösung)."""
    return tuple(i for i, v in enumerate(solution.x) if v > 1 - C.TOL)


@dataclass(frozen=True)
class RoundStep:
    edge: int               # die auf 1 gesetzte Leitung
    value: float            # ihr Wert im Programm (mindestens 1/2)
    lp_value: float         # Kosten des Programms vor diesem Schritt


@dataclass(frozen=True)
class Rounding:
    chosen: tuple           # Indizes der gewählten Leitungen
    cost: int
    steps: tuple            # RoundStep je Schritt
    lp_first: float         # Kosten des ersten Programms (untere Schranke)
    guarantee_held: bool    # gab es in jedem Schritt eine Leitung mit Wert ≥ 1/2?


def iterative_rounding(n, edges, costs, max_steps=None):
    """Iteratives Runden nach Jain: Programm lösen, die Leitung mit dem größten Wert (mindestens 1/2; Gleichstand: kleinere Nummer) auf 1 setzen, wiederholen, bis die gewählten Leitungen 2-Kanten-zusammenhängend sind."""
    m = len(edges)
    fixed, steps = [], []
    lp_first = None
    held = True
    limit = max_steps or m
    while len(steps) <= limit:
        if fixed and is_two_edge_connected(adj_from_edges(n, [edges[i] for i in fixed])):
            break
        sol = solve_cover(n, edges, costs, fixed=fixed)
        if lp_first is None:
            lp_first = sol.value
        free = [i for i in range(m) if i not in set(fixed)]
        best = max(free, key=lambda i: (round(sol.x[i], 9), -i))
        if sol.x[best] < C.HALF:
            held = False
        steps.append(RoundStep(best, sol.x[best], sol.value))
        fixed.append(best)
    chosen = tuple(sorted(fixed))
    return Rounding(chosen, int(sum(costs[i] for i in chosen)), tuple(steps), float(lp_first if lp_first is not None else 0.0), held)


# --- Kritische Kantenpaare ------------------------------------------------------------------------------------------------------------------------


def critical_pairs(adj):
    """Paare von Leitungen, deren gemeinsamer Ausfall das Netz trennt, ohne dass eine von ihnen schon allein eine Brücke ist."""
    br = set(bridges(adj))
    pairs = set()
    for e in edges_of(adj):
        if e in br:
            continue
        for f in bridges(adj, removed={e}):
            if f != e and f not in br:
                pairs.add(tuple(sorted((e, f))))
    return tuple(sorted(pairs))


def comb2(m):
    return m * (m - 1) // 2


def isclose(a, b):
    return math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9)

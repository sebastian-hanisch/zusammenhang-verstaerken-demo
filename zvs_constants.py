"""Konstanten: Regler-Grenzen, feste Annahmen, Experiment-Raster, Farben und Presets."""

KINDS = ("textbook", "random", "grid", "ring", "scalefree", "verbund", "geometric")
KIND_NAMES = {"textbook": "Lehrbeispiel (Ring mit Anhängseln)", "random": "Zufallsnetz", "grid": "Gitter", "ring": "Ring mit Abkürzungen", "scalefree": "Skalenfreies Netz", "verbund": "Verbundnetz",
              "geometric": "Kartennetz"}
KIND_HELP = {
    "textbook": "Zehn Standorte, von Hand zu prüfen: ein Ring mit vier Anhängseln, jedes über eine Brücke.",
    "random": "Zufallsbaum plus zufällige Leitungen; der mittlere Grad ist einstellbar (bei kleinem Grad viele Brücken).",
    "grid": "Standorte auf einem Raster, Verbindungen zu den vier Nachbarn (brückenfrei).",
    "ring": "Vier nächste Nachbarn auf einem Ring, ein Zehntel der Leitungen führt zu einem zufälligen Standort.",
    "scalefree": "Neue Standorte hängen sich bevorzugt an gut vernetzte an (je zwei Leitungen).",
    "verbund": "Drei Regionen mit dichten inneren Verbindungen und wenigen Leitungen dazwischen (einstellbar).",
    "geometric": "Zufällige Punkte in einem Quadrat, jeder mit seinen drei nächsten Nachbarn verbunden: ein Straßennetz im Kleinen.",
}
KIND_REGLER = {
    "textbook": "Das Lehrbeispiel ist fest: Standorte, Grad und Leitungen wirken nicht; die Kosten der Leitungen kommen aus dem Zufalls-Seed.",
    "random": "Wirksam: Standorte, mittlerer Grad, Zufalls-Seed (auch für die Kosten).",
    "grid": "Wirksam: Standorte (gerundet auf ein Rechteck), Zufalls-Seed (nur für die Kosten). Grad und Leitungen wirken nicht.",
    "ring": "Wirksam: Standorte, Zufalls-Seed (Netz und Kosten).",
    "scalefree": "Wirksam: Standorte, Zufalls-Seed (Netz und Kosten).",
    "verbund": "Wirksam: Standorte, mittlerer Grad (in den Regionen), Leitungen zwischen den Regionen, Zufalls-Seed (Netz und Kosten).",
    "geometric": "Wirksam: Standorte, Zufalls-Seed (Netz und Kosten).",
}

N_MIN, N_MAX, DEFAULT_N = 8, 40, 10
DEG_MIN, DEG_MAX, DEFAULT_DEG = 2.0, 10.0, 4.0
LINKS_MIN, LINKS_MAX, DEFAULT_LINKS = 1, 8, 2
SEED_MAX, DEFAULT_SEED = 999999, 7
DEFAULT_KIND = "textbook"
REGIONS = 3
RING_NEIGHBOURS, RING_REWIRE = 4, 0.1
SCALEFREE_M = 2
COST_MAX = 9                             # Kosten je Leitung: ganze Zahlen 1 bis COST_MAX
BRUTE_N = 14                             # größte Netzgröße für die exakte Lösung (Mischung aus ganzzahligem Programm und nachgeladenen Schnittbedingungen)
TOL = 1e-7                               # Toleranz für Schnittwerte und Ganzzahligkeit des linearen Programms
HALF = 0.5 - 1e-7                        # Schwelle für das Runden: ein Wert ab 1/2 wird auf 1 gesetzt
PERTURB = 1e-4                           # Störung der Kosten (je Leitung verschieden), damit das lineare Programm eine eindeutige Ecke hat

SWEEP_SEEDS = tuple(range(100000, 100008))   # feste Netze für alle Experimente: nie ein einzelner Zufalls-Seed als Befund
EX_N = 12
EX_KINDS = (("random", 3.0), ("random", 6.0), ("grid", 0.0), ("ring", 0.0), ("scalefree", 0.0), ("verbund", 5.0), ("geometric", 0.0))
EX_AUG_N = 16                            # Netzgröße für das Verstärken (Quadratzahl: das Gitter hat dieselbe Größe), Netze mit wenig Leitungen
EX_AUG_SEEDS = 12
EX_AUG_DEG = 2.5                         # mittlerer Grad der Netze, an denen das Verstärken gemessen wird (viele Brücken)

COLOR_SIDE_A = "#2F6B65"
COLOR_SIDE_B = "#4c78a8"
COLOR_CUT = "#d1495b"
COLOR_NODE = "#c9d1d3"
COLOR_EDGE = "rgba(150,150,150,0.55)"
COLOR_BAR = "#4c78a8"
COLOR_BAR2 = "#e8a33d"
COLOR_BAR3 = "#2F6B65"
COLOR_LOCK = "#8d6cab"
COLOR_BRIDGE = "#d1495b"
COLOR_NEW = "#2F6B65"
COLOR_CHOSEN = "#2F6B65"
COLOR_FRACTION = "#e8a33d"

PRESETS = {
    "Lehrbeispiel (Ring mit Anhängseln)": {"kind": "textbook", "n": DEFAULT_N, "deg": DEFAULT_DEG, "links": DEFAULT_LINKS, "seed": DEFAULT_SEED},
    "Der Vertreter ist nicht der Endpunkt": {"kind": "random", "n": 10, "deg": 2.5, "links": DEFAULT_LINKS, "seed": 62},
    "Das Gitter braucht nichts": {"kind": "grid", "n": 12, "deg": DEFAULT_DEG, "links": DEFAULT_LINKS, "seed": 1},
    "Redundanz kostet mehr als ein Spannbaum": {"kind": "ring", "n": 12, "deg": DEFAULT_DEG, "links": DEFAULT_LINKS, "seed": 2},
    "Das Runden verfehlt das Optimum": {"kind": "ring", "n": 12, "deg": DEFAULT_DEG, "links": DEFAULT_LINKS, "seed": 13},
    "Der Entwurf ist ein einziger Kreis": {"kind": "random", "n": 12, "deg": 6.0, "links": DEFAULT_LINKS, "seed": 3},
    "Größeres Netz: nur das Programm": {"kind": "geometric", "n": 30, "deg": DEFAULT_DEG, "links": DEFAULT_LINKS, "seed": 5},
}
PRESET_HELP = {
    "Lehrbeispiel (Ring mit Anhängseln)": "Zehn Standorte, vier Brücken, vier Blätter im Brückenbaum: zwei neue Leitungen genügen (von Hand zu prüfen).",
    "Der Vertreter ist nicht der Endpunkt": "Ein Einzelstandort hängt über eine Brücke am Rest: Der Vertreter des großen Blatts darf nicht der Endpunkt der Brücke sein, sonst entstünde die Leitung ein zweites Mal.",
    "Das Gitter braucht nichts": "Ein Gitter hat keine Brücke; der Tab Verstärken hat nichts zu tun, der Entwurf wählt aus den Gitterleitungen die billigste 2-Kanten-zusammenhängende Teilmenge.",
    "Redundanz kostet mehr als ein Spannbaum": "Ring mit Abkürzungen: Das billigste 2-Kanten-zusammenhängende Teilnetz kostet 35, der billigste Spannbaum 21 (das 1,67-Fache).",
    "Das Runden verfehlt das Optimum": "Das lineare Programm ist gebrochen, iteratives Runden kostet 49 statt 46 (das 1,07-Fache, die Garantie ist 2).",
    "Der Entwurf ist ein einziger Kreis": "Das billigste Teilnetz ist ein Kreis über alle zwölf Standorte: Jedes der 66 Leitungspaare trennt es, im ganzen Kandidatennetz nur eines von 630.",
    "Größeres Netz: nur das Programm": "30 Standorte, keine exakte Lösung mehr: Das lineare Programm (136) ist die untere Schranke, iteratives Runden kostet 138.",
}

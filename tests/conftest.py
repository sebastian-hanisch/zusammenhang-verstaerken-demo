"""Gemeinsame Fixtures: die Mini-Netze, an denen jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b).

Teure Experimente laufen einmal je Testlauf (`lru_cache`) und werden von Claims-, Verdikt- und Mutationstests gemeinsam genutzt."""

import sys
from functools import lru_cache
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def adj_of(n, pairs):
    nb = [set() for _ in range(n)]
    for u, v in pairs:
        nb[u].add(v)
        nb[v].add(u)
    return tuple(tuple(sorted(s)) for s in nb)


# Verstärken, von Hand gerechnet: Name -> (n, Leitungen, Brücken, 2-Kanten-Zusammenhangskomponenten, Blätter in Tiefensuch-Reihenfolge (Indizes der Komponenten), neue Leitungen, davon naiv parallel)
AUG = {
    "lehrbeispiel": (10, [(0, 1), (1, 2), (2, 3), (0, 3), (0, 4), (2, 5), (1, 6), (6, 7), (7, 8), (6, 8), (3, 9)], ((0, 4), (1, 6), (2, 5), (3, 9)),
                     ((0, 1, 2, 3), (4,), (5,), (6, 7, 8), (9,)), (1, 2, 3, 4), ((4, 7), (5, 9)), 0),
    "pfad4": (4, [(0, 1), (1, 2), (2, 3)], ((0, 1), (1, 2), (2, 3)), ((0,), (1,), (2,), (3,)), (0, 3), ((0, 3),), 0),
    "stern": (4, [(0, 1), (0, 2), (0, 3)], ((0, 1), (0, 2), (0, 3)), ((0,), (1,), (2,), (3,)), (1, 2, 3), ((1, 2), (2, 3)), 0),
    "fahne": (4, [(0, 1), (1, 2), (1, 3), (2, 3)], ((0, 1),), ((0,), (1, 2, 3)), (0, 1), ((0, 2),), 1),                                  # Standort 0 hängt über eine Brücke an einem Dreieck
    "kreis6": (6, [(v, (v + 1) % 6) for v in range(6)], (), ((0, 1, 2, 3, 4, 5),), (), (), 0),
}

# Entwurf: zwei Dreiecke (Leitungen zu 1) und zwei Verbindungen (0-5 und 2-3, Kosten 3); ohne die Schnittbedingung für ein Dreieck wählt das Programm nur die Dreiecke (Kosten 6)
DREIECKE = (6, [(0, 1), (0, 2), (0, 5), (1, 2), (2, 3), (3, 4), (3, 5), (4, 5)], [1, 1, 3, 1, 3, 1, 1, 1])

# Quadrat mit Diagonale: vier Leitungen zu 1 und die Diagonale zu 5 (Leitungen sortiert: (0,1) (0,2) (0,3) (1,2) (2,3))
QUADRAT = (4, [(0, 1), (0, 2), (0, 3), (1, 2), (2, 3)], [1, 5, 1, 1, 1])


@pytest.fixture
def mini():
    return AUG


@lru_cache(maxsize=None)
def cached(name):
    """Einmal je Testlauf berechnete Experimente (Name der Funktion in zvs_experiments)."""
    import zvs_experiments as ex
    return getattr(ex, name)()


class FixedRandom:
    """Liefert immer fast 1: Fisher–Yates lässt die Reihenfolge unverändert."""

    def random(self):
        return 0.999999

# Zusammenhang verstärken und Netze entwerfen – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-zusammenhang-verstaerken-demo.streamlit.app/)**

Viertes Stück der Reihe **Schnitte und Zusammenhang** (Arbeitstitel der Linie `schnitte-zusammenhang`) in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“, Bereich Graphentheorie. Vehikel: ein **Verbindungsnetz zwischen Standorten** (Depots, Umschlagpunkte, Werke), synthetisch und mit festem Zufalls-Seed. Die Demo fragt: **Welche Leitungen fehlen, damit kein einzelner Ausfall das Netz trennt, und was kostet das?** Eine **Brücke** ist eine Leitung, deren Ausfall das Netz zerlegt; ein Netz ohne Brücke ist **2-Kanten-zusammenhängend**. Zwei Aufgaben: **Verstärken** (ein vorhandenes Netz mit möglichst wenigen neuen Leitungen brückenfrei machen: die Blätter des Brückenbaums paarweise verbinden) und **Entwerfen** (aus Kandidatenleitungen mit Kosten die billigste brückenfreie Auswahl treffen; NP-schwer) mit einem **linearen Programm mit nachgeladenen Schnittbedingungen**, **iterativem Runden** (Garantie 2) und der **exakten** Lösung als Maßstab. Ein dritter Tab zählt **Doppelausfälle**: Leitungspaare, deren gemeinsamer Ausfall das Netz trennt.

Nachbarn: Brücken zählt `bridges-demo`, den Zusammenhang über disjunkte Wege `menger-demo`, Schnittbedingungen für **Flusskapazitäten** nachzuladen `fixkosten-netzdesign-demo`, den billigsten Spannbaum `mst-sensitivity-demo`.

## Warum dieses Problem

Ein Netz, in dem eine einzige Leitung ausfallen darf, ohne dass es zerfällt, braucht Redundanz, und die kostet. Die Demo zeigt, **wie einfach das Verstärken ist** (⌈L / 2⌉ neue Leitungen bei L Blättern, in allen gemessenen Netzen erreicht), **wo die Konstruktion heikel ist** (die Wahl des Vertreters im Blatt), **dass das billigste 2-Kanten-zusammenhängende Teilnetz das Eineinhalbfache eines Spannbaums kostet**, **dass das lineare Programm dabei fast ganzzahlig ist und das Runden fast immer das Optimum trifft**, und **dass der billigste Entwurf verwundbar ist**: In 27 von 56 Netzen ist er ein einziger Kreis, in dem jedes Paar von Leitungen das Netz trennt.

## Befunde und Korrekturen gegenüber dem Plan

- **Die Vormessungszahlen gelten nicht:** „Redundanz kostet 56 bis 67 % mehr als ein Spannbaum“, „Lücke zum linearen Programm höchstens 1,02“, „Runden im Mittel 4 bis 5 % über dem Optimum, im schlechtesten Fall 39 %“ stammen aus Wegwerfskripten mit anderen Netzen. Die Demo misst neu (Tabelle unten): das Optimum kostet im Mittel das **1,53-Fache** des Spannbaums (je Netztyp 1,36 bis 1,82), die Lücke ist höchstens **1,05**, das Runden liegt im Mittel **0,5 %** über dem Optimum und im schlechtesten Netz **10 %** darüber.
- **Löser bis 14 Standorte, dann nur das Programm:** Der Plan hielt für n ≥ 14 einen Löser mit Rückruf oder CP-SAT für nötig. Die Demo löst das ganzzahlige Programm mit denselben **nachgeladenen Schnittbedingungen** (jeweils wieder lösen, den kleinsten Schnitt suchen, hinzufügen) und kommt bei 12 Standorten mit im Mittel **einem** nachgeladenen Schnitt aus (von 2.047); über 14 Standorten bleibt das lineare Programm als untere Schranke.
- **Die Jain-Schwelle ½ hält:** In **jedem** Schritt aller 56 Netze gab es eine Leitung mit Wert mindestens ½; die Vermutung des Plans, die Schwelle werde sichtbar eng, bestätigt sich nicht (nicht gemessen, wie oft der gewählte Wert genau 1 ist).
- **Vertreterwahl:** Mit dem kleinsten Standort eines Blatts als Vertreter entstand die neue Leitung in **1 von 26** Netzen mit Brücken ein zweites Mal parallel zu einer vorhandenen (Plan: 7 von 239); die Demo wählt einen Standort, der nicht Endpunkt der Brücke ist.
- **Kosten-Variante des Verstärkens nicht gebaut:** Der Plan nannte „Greedy gegen exakt“ für das Verstärken mit Kosten; das gewichtete Verstärken eines vorhandenen Netzes ist ein eigener NP-schwerer Fall. Gebaut ist das Verstärken ohne Kosten und der Entwurf mit Kosten, in dem ein Netz mit Brücken zuerst um die Verstärkung ergänzt wird.
- **Doppelausfälle:** Der Plan sah sie als Tab vor; neu ist der Befund, dass der **billigste Entwurf** viel verwundbarer ist als das Kandidatennetz (60 gegen 1 % der Leitungspaare).

## Modell

Ein einfaches, **zusammenhängendes** Netz mit n Standorten (Zufallsnetz: Zufallsbaum plus Leitungen bis zum mittleren Grad, bei kleinem Grad viele Brücken; Gitter als Rechteck, Ring mit Abkürzungen, skalenfreies Netz nach bevorzugter Anbindung, Verbundnetz mit drei Regionen und einstellbar vielen Leitungen dazwischen, Kartennetz aus zufälligen Punkten) und das handgebaute **Lehrbeispiel Ring mit Anhängseln**: ein Ring aus vier Standorten, daran über **Brücken** drei Einzelstandorte und ein Dreieck. Von Hand: vier Brücken; die brückenfreien Teile sind der Ring, das Dreieck und die drei Einzelstandorte; der Brückenbaum ist ein Stern mit **vier Blättern**, also genügen und braucht man ⌈4 / 2⌉ = **2** neue Leitungen. Jede Leitung bekommt Kosten, ganze Zahlen von 1 bis 9 (Zufalls-Seed). **Kandidatennetz** des Entwurfs: die Leitungen des Netzes; hat es Brücken, kommen die Leitungen der Verstärkung dazu, damit es überhaupt eine brückenfreie Lösung gibt. Der Zufall kommt nur aus `random.Random(seed)` mit `random()` (plattformstabil). Details und Formeln: Expander „📐 Mathematische Formulierung“ in der App.

## Methodik

- **Brücken:** Tiefensuche mit Low-Werten (iterativ). **Brückenbaum:** Brücken entfernen, die Komponenten bilden die Punkte; Blätter in Tiefensuch-Reihenfolge von der ersten inneren Komponente aus.
- **Verstärken:** Blatt i mit Blatt i + ⌊L / 2⌋ verbinden, i = 1 .. ⌈L / 2⌉ (Eswaran, Tarjan); Vertreter eines Blatts: der kleinste Standort, der nicht Endpunkt der Brücke ist (bei einer Komponente aus einem Standort dieser). Die untere Schranke ⌈L / 2⌉ ist zugleich die Zahl der neuen Leitungen.
- **Entwerfen, lineares Programm:** x_e in [0, 1], je Schnitt x(δ(S)) ≥ 2; gestartet wird mit den n Gradbedingungen, dann wird gelöst (HiGHS, Ecke), der kleinste Schnitt der Lösung gesucht (Stoer–Wagner mit den Werten als Gewichten) und, wenn er unter 2 liegt, als Bedingung hinzugenommen. Die Kosten sind für das Programm leicht gestört (je Leitung verschieden, höchstens 1e-4), damit die Ecke eindeutig ist; angezeigt werden die echten Kosten.
- **Exakt:** dasselbe mit ganzzahligen Variablen (`scipy.optimize.milp`) bis 14 Standorte. **Spannbaum:** Kruskal.
- **Iteratives Runden (Jain):** Programm lösen (mit den schon gewählten Leitungen als Wert 1), die Leitung mit dem größten Wert (mindestens ½, bei Gleichstand die kleinere Nummer) wählen, wiederholen, bis die gewählten Leitungen 2-Kanten-zusammenhängend sind. Die Kosten sind höchstens doppelt so hoch wie die des ersten Programms.
- **Doppelausfälle:** zwei Leitungen, die keine Brücken sind, heißen kritisch, wenn die zweite im Netz ohne die erste eine Brücke ist (je Leitung eine Brückensuche).
- **Unabhängige Prüfer:** Die App prüft jedes Ergebnis vor der Anzeige (nach der Verstärkung brückenfrei und ⌈L / 2⌉ neue Leitungen, keine doppelt; Kandidatennetz brückenfrei; Spannbaum; Lösung des Programms in [0, 1] und kein Schnitt unter 2; Optimum und Runden 2-Kanten-zusammenhängend und mit nachgezählten Kosten; Programm nie über dem Optimum, Optimum nie unter einem Spannbaum, Runden nie unter dem Optimum und nie über dem Doppelten des Programms).

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen stehen in `tests/test_claims.py`; Zähler über feste Netze (Verstärken: je Netztyp zwölf Netze mit 16 Standorten und mittlerem Grad 2,5; Entwurf: je Netztyp acht Netze mit 12 Standorten), nie ein einzelner Zufalls-Seed. Netztypen beim Entwurf: Zufallsnetz mit mittlerem Grad 3 und 6, Gitter, Ring mit Abkürzungen, skalenfreies Netz, Verbundnetz (mittlerer Grad 5, eine Leitung zwischen je zwei Regionen), Kartennetz.

| Frage | Befund |
|---|---|
| Wie oft haben die Netze Brücken, und was kostet das Verstärken? | Von **72** Netzen (sechs Netztypen, 16 Standorte, mittlerer Grad 2,5) haben **26** Brücken: Zufallsnetz **12 von 12**, Verbundnetz **10**, Kartennetz **4**, Gitter, Ring und skalenfreies Netz **0**. Es sind **79** Brücken (im Mittel 3,0 je Netz mit Brücken); die Brückenbäume haben **76** Blätter und brauchen **41** neue Leitungen: in allen 26 Netzen genau ⌈L / 2⌉ und brückenfrei danach. |
| Ist die Vertreterwahl wichtig? | Mit dem kleinsten Standort des Blatts als Vertreter wäre in **1 von 26** Netzen mit Brücken eine neue Leitung parallel zu einer vorhandenen (hier einer Brücke); mit einem Standort, der nicht Endpunkt der Brücke ist, in **keinem**. |
| Was kostet Redundanz gegenüber einem Spannbaum? | Das Optimum (billigstes 2-Kanten-zusammenhängendes Teilnetz) kostet auf **56** Netzen im Mittel das **1,53-Fache** des billigsten Spannbaums (3.105 gegen 2.031): je Netztyp **1,36** (Gitter) bis **1,82** (skalenfrei). |
| Wie ganzzahlig ist das lineare Programm? | Die Lücke Optimum / Programm ist höchstens **1,05** (Ring mit Abkürzungen; Summe der Kosten 3.105 gegen 3.101,5); die Lösung des Programms ist in **47 von 56** Netzen ganzzahlig. |
| Wie gut ist das iterative Runden? | Es trifft das Optimum in **50 von 56** Netzen und kostet im Mittel das **1,005-Fache** (3.119 gegen 3.105), im schlechtesten Netz das **1,10-Fache** (Ring mit Abkürzungen); die Garantie 2 erreicht kein Netz. In jedem Schritt gab es eine Leitung mit Wert mindestens ½. |
| Wie viele Schnittbedingungen muss man nachladen? | Von **2.047** möglichen (bei 12 Standorten) im Mittel **1** (insgesamt **56** auf 56 Netzen, höchstens **5**; Verbundnetz 21, Kartennetz 14), bei im Mittel **2** Lösungen des Programms. Die zwölf Gradbedingungen stehen von Anfang an dabei. |
| Wie verwundbar ist der billigste Entwurf? | Im ganzen Kandidatennetz trennen **147 von 15.038** Leitungspaaren (**1 %**) das Netz, im billigsten Entwurf **2.613 von 4.360** (**60 %**). In **27 von 56** Netzen ist der Entwurf ein einziger Kreis über alle Standorte (Zufallsnetz Grad 6, Gitter, Ring und Kartennetz je 6 von 8): dann trennt jedes Paar. |
| Das Lehrbeispiel von Hand? | Ring mit Anhängseln, 10 Standorte, 11 Leitungen: **4 Brücken**, Brückenbaum mit **5 Komponenten und 4 Blättern**, **2** neue Leitungen (5–8 und 6–10 im Kern 4–7 und 5–9); Kandidatennetz 13 Leitungen, Spannbaum **27**, Optimum **39** (das lineare Programm ist ganzzahlig, das Runden trifft es). |
| Sind die Preset-Beschreibungen belegt? | Ja, jedes Preset in `tests/test_claims.py` (z. B. „Redundanz kostet mehr als ein Spannbaum“: 35 gegen 21, das 1,67-Fache; „Das Runden verfehlt das Optimum“: 49 statt 46). |
| Ist die Rechnung korrekt? | Brücken gleich `networkx.bridges` (60 Netze und die Mini-Netze), Zahl der neuen Leitungen gleich dem Optimum von `networkx.k_edge_augmentation` (80 Netze); Spannbaum gleich `networkx.minimum_spanning_tree`; der gewichtete Schnitt gleich `networkx.stoer_wagner`; das Programm mit nachgeladenen Schnitten gleich dem vollständigen Programm mit allen 2^(n−1) − 1 Bedingungen (`scipy.optimize.linprog`, 20 Netze) und zulässig für jeden Schnitt; das Optimum gleich der Aufzählung aller Leitungsmengen (Netze mit höchstens 13 Kandidaten); Runden zulässig, nie unter dem Optimum und höchstens doppelt so teuer wie das Programm (40 Netze); kritische Paare gleich der Aufzählung aller Leitungspaare (24 Netze) (`tests/test_oracle_verstaerken.py`). |

## Ehrliche Grenzen

- **Nur Leitungsausfälle, nur Zusammenhang 2.** Der Ausfall von Standorten (Knotenzusammenhang) und höhere Ziele oder Anforderungen je Paar (Steinernetz-Entwurf) sind nicht gebaut.
- **Zufällige Kosten.** Die Kosten sind ganze Zahlen von 1 bis 9 aus dem Zufalls-Seed; echte Trassenkosten hängen von Länge und Gelände ab. Die Befunde zum Verhältnis zum Spannbaum und zum Runden gelten für diese Kosten und Netze.
- **Kleine Netze beim Messen.** Die Zählungen zum Entwurf laufen auf Netzen mit 12 Standorten (die exakte Lösung bis 14, das Programm und das Runden bis 40); ob das Runden auf großen Netzen genauso nahe am Optimum liegt, ist nicht gemessen.
- **Das Runden hängt an der Ecke des Programms.** Die Zahlen dazu (50 von 56) gelten für die Ecke, die HiGHS mit den gestörten Kosten findet; eine andere Ecke bei gleichen Kosten kann zu anderen Wahlen führen (die Garantie bleibt).
- **Kein Verstärken mit Kosten.** Das Verstärken zählt neue Leitungen; mit Kosten je Kandidat wäre es der NP-schwere Entwurf mit vorhandenem Netz.
- **Doppelausfälle gleich wahrscheinlich.** Ein kritisches Paar zählt wie jedes andere; Wahrscheinlichkeiten und Abhängigkeiten der Ausfälle sind nicht modelliert.
- **Größe:** bis 40 Standorte.

## Tests

Das Verzeichnis `tests/` enthält zurzeit 128 Tests (Laufzeit etwa 25 Sekunden auf dem Entwicklungsrechner):

- **Kern** (`test_algorithm.py`): jede Einheit an von Hand gerechneten Mini-Netzen (Lehrbeispiel, Pfad, Stern, Fahne, Kreis; zwei Dreiecke mit Verbindungen, Quadrat mit Diagonale): Brücken, Brückenbaum, Tiefensuch-Reihenfolge der Blätter, Paarung, Vertreter, Spannbaum, gewichteter Schnitt, Programm mit einem nachgeladenen Schnitt, feste Leitungen, Runden Schritt für Schritt, kritische Paare.
- **Szenarien** (`test_scenario.py`): einfach, zusammenhängend, deterministisch für jeden Netztyp; Lehrbeispiel; Kosten.
- **Orakel** (`test_oracle_verstaerken.py`): networkx (Brücken, Verstärkung, Spannbaum, gewichteter Schnitt), vollständiges Programm, Aufzählung aller Leitungsmengen und aller Leitungspaare.
- **Randfälle** (`test_edge_cases.py`): zwei und drei Standorte, Pfad und Stern, alle Kandidaten nötig, Gleichstände, jede Art von Prüffehler an verfälschten Analysen, Grenzen.
- **Zweige, Verdikte, Befunde** (`test_branches.py`, `test_verdicts.py`, `test_claims.py`): jedes Preset löst seine Beschreibung ein und jede Abbildung rendert; jedes Verdikt an handgesetzten Zeilen; jede Zahl dieses README.
- **Oberfläche:** AppTest-Rauchtest (jeder Button, jeder Regler am Minimum und Maximum), Layout (Schnellstart oben, aktives Preset hervorgehoben), Footer, Laufzeit-Importe.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App: Verstärken, Entwerfen, Doppelausfälle, vier Experimente |
| `requirements-dev.txt` | Laufzeit plus pytest und networkx (Gegenproben) |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt), darunter scipy für das lineare und das ganzzahlige Programm |
| `zvs_algorithm.py` | Kern: Brücken, Brückenbaum, Verstärkung, Spannbaum, gewichteter Schnitt, Programm mit nachgeladenen Schnitten, Runden, kritische Paare |
| `zvs_constants.py` | Regler-Grenzen, Netztypen, Raster der Experimente, Farben, Presets |
| `zvs_evaluation.py` | Analyse, Kandidatennetz, Prüfung vor der Anzeige, Verdikte |
| `zvs_experiments.py` | Experimente über feste Netze |
| `zvs_layout.py` | Fester Kopf (Stylesheet) |
| `zvs_presets.py` | Permalink, Presets (Schnellstart in der Seitenleiste, aktives Preset hervorgehoben), Zufalls-Seed-Button |
| `zvs_scenario.py` | Netze: Lehrbeispiel, Zufallsnetz, Gitter, Ring, skalenfreies Netz, Verbundnetz, Kartennetz; Kosten |
| `zvs_visualization.py` | Plotly-Abbildungen (Karten mit Brücken, Kandidaten, Programmwerten und Doppelausfällen, Experimente; Achsen gesperrt) |
| `tests/` | Mini-Netze, Orakel, Randfälle, Zweige, Verdikte, Befunde, Presets, Layout, AppTest, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Verstärken mit Kosten, höhere Zusammenhangsziele, Knotenzusammenhang, Steinernetz-Entwurf:** nur als Einordnung in der Formulierung.
- **Echte Netze oder Dateiimport:** die Netze sind synthetisch.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, pandas und SciPy.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).

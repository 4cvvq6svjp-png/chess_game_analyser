# chess_game_analyser

Moteur d'échecs écrit en Python pur, sans dépendance. Jouable au terminal en
1v1 local ; destiné à devenir un jeu complet (API + interface web, IA, analyse
de parties).

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Jouer

```bash
chess-game
```

ou, sans installer le script :

```bash
python -m chess_engine.main
```

Les coups se saisissent sous la forme `case_départ/case_arrivée`, par exemple
`e2/e4`. La promotion d'un pion demande la pièce souhaitée dans le terminal.

## L'API

L'API HTTP est un paquet à part (`chess_api`), installé par l'extra `[api]` :
le moteur, lui, reste sans dépendance.

```bash
pip install -e ".[dev,api]"
uvicorn chess_api.app:app --reload
```

Quatre endpoints sous `/api/v1/games` : créer, lire, jouer un coup,
abandonner. La documentation interactive est servie sur
`http://localhost:8000/docs` ; le contrat complet est dans
[`docs/api-contract.md`](docs/api-contract.md).

## Tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```

`CHESS_SLOW_TESTS=1` ajoute perft en profondeur 4 (~20 s). Les tests de l'API
sont ignorés si l'extra `[api]` n'est pas installé.

## Structure

| Chemin | Rôle |
|---|---|
| `src/chess_engine/game_position.py` | `GamePosition` : une position immuable, ses coups légaux, FEN, SAN, verdict |
| `src/chess_engine/game.py` | `Game` : position de départ + coups ; historique, répétition, abandon, forme durable |
| `src/chess_engine/document.py` | le document de partie servi par l'API |
| `src/chess_engine/errors.py` | les refus typés (`IllegalMove`, `GameOver`…) |
| `src/chess_engine/move.py` | `Move` et la notation longue (`e2e4`) |
| `src/chess_engine/{pawn,knight,bishop,rook,queen,king}.py` | une classe par pièce, géométrie des coups |
| `src/chess_engine/perft.py` | le comptage de nœuds qui prouve les règles |
| `src/chess_engine/cli.py` | le jeu au terminal |
| `src/chess_api/` | l'API HTTP (FastAPI) et le stockage des parties |
| `tests/` | suite `unittest`, dont perft et un corpus de parties réelles rejouées |
| `tools/` | fabrication du corpus (avec `python-chess` comme oracle) |
| `docs/` | roadmap, contrat d'API, revues de code, journal de bord |

**Convention de coordonnées** : `board[row][col]`, avec `row 0` = rang 8 (haut du
plateau) et `col 0` = colonne `a`.

## État actuel

Règles complètes : les six pièces, roque, prise en passant, promotion, mat,
pat, 50 coups, répétition triple, matériel insuffisant, abandon — vérifiées
par perft et par des parties réelles rejouées.

API en mémoire (phase 2.2). À venir : persistance SQLite, horloge, puis le
front React. Le détail est dans le roadmap.

## Documentation

- [`docs/roadmap.md`](docs/roadmap.md) — état des lieux, architecture cible et
  découpage en phases
- [`docs/code-review-2026-06.md`](docs/code-review-2026-06.md) — revue de code et
  bugs corrigés
- [`docs/chess-logic-todo.md`](docs/chess-logic-todo.md) — dette de règles connue
- [`docs/journal-de-bord.md`](docs/journal-de-bord.md) — notes de développement

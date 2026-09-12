# Roadmap — de moteur terminal à jeu d'échecs complet (React + API)

Document de planification. État des lieux du code existant, blocages
structurels identifiés, architecture cible et découpage en phases.

Compagnon de [`code-review-2026-06.md`](./code-review-2026-06.md) (bugs déjà
corrigés) et [`chess-logic-todo.md`](./chess-logic-todo.md) (dette de règles).

---

## 1. État des lieux

~1 380 lignes de Python, stdlib uniquement, zéro dépendance, jeu jouable au
terminal. 51 tests `unittest`, tous verts.

### Architecture actuelle

| Module | Rôle |
|---|---|
| `pieces.py` | `Piece` (ABC) : `_is_valid_move`, `_move_piece(add\|remove)`, `_can_move`, `_execute_move` |
| `pawn/knight/bishop/rook/queen/king.py` | une classe par pièce, valident un coup **proposé** |
| `move_utility.py` | ray-walking statique : `check_diags/lines/horses`, `reach_sqr_*` |
| `chess_board.py` | matrice 8×8 `list[list[Piece\|None]]`, `play_stack`, détection échec/mat/pat, affichage |
| `chess_game.py` | boucle de jeu, parsing `"a1/a3"`, rejet de l'auto-échec par `deepcopy` |
| `player.py` | `input()` terminal |

Convention de coordonnées : `board[row][col]`, `row 0` = rang 8, `col 0` = colonne a.

### Conventions surprenantes à connaître avant de toucher au code

- Les `check_*` renvoient `{"check": False}` quand la case **est** attaquée. Le
  booléen est inversé par rapport à son nom.
- `is_in_check` compte les `True` : 3 = pas d'échec, ≤ 1 = échec double.
- Le cavalier porte le nom `"horse"`, mais `create_piece_by_name` attend
  `"knight"` → une promotion en cavalier produit une pièce nommée `"horse"`.
- `_move_piece(..., "add")` **recrée une nouvelle instance** de la pièce.
  L'identité de l'objet est perdue à chaque coup.

### Ce qui marche

Déplacements de base, prise en passant (validation pure + exécution séparée),
promotion via prompt, détection d'échec (y compris double et roi adverse
adjacent), rejet de l'auto-échec dans la boucle de jeu, mat simple, pat.

---

## 2. Les cinq blocages structurels

Ce ne sont pas des bugs : c'est ce qui empêche mécaniquement les features visées.

1. **Pas de générateur de coups légaux.** Tout le moteur répond à « ce coup
   est-il valide ? », jamais à « quels sont les coups possibles ? ». Or l'API,
   le front (pastilles de coups), l'IA, l'import PGN et le rewind ont *tous*
   besoin de `legal_moves(position) -> list[Move]`. C'est **la** pièce manquante.
2. **Règles et I/O entremêlées.** `launch_game()` appelle `input()`/`print()` au
   milieu de la logique de promotion et de fin de partie. Rien n'est pilotable
   depuis une API.
3. **Pas de sérialisation de position (FEN).** Sans elle : pas de rewind, pas de
   répétition triple, pas d'échange client/serveur, pas d'UCI/Stockfish, pas
   d'import.
4. **Identité des pièces détruite à chaque coup** → impossible de porter un flag
   `has_moved` → le roque est bloqué par construction.
5. **Imports plats** (`from chess_board import Board`) → le code n'est importable
   qu'en manipulant `sys.path`. Non packageable, donc pas consommable
   proprement par un serveur web.

---

## 3. Bugs de règles confirmés (reproduits)

| # | Symptôme | Statut |
|---|---|---|
| 1 | **King-shadow** : `Ke1` face à `Ta1`, le roi « glisse » en `f1`. Sa propre case n'est pas vidée avant d'évaluer les fuites → faux « pas mat ». | reproduit |
| 2 | **Clouages ignorés** dans `is_it_checkmate` et `_can_move`/`_is_pat` : un cavalier cloué compte comme ayant un coup. La boucle de jeu, elle, filtre correctement (deepcopy) — l'incohérence est entre les deux chemins. | reproduit |
| 3 | **Roque absent.** | reproduit |
| 4 | `_is_stalemate` = `play_stack[:4] == play_stack[4:]` : vrai seulement au demi-coup 8, et ce n'est pas la répétition triple. | lecture |
| 5 | Règle des 50 coups, matériel insuffisant : absents. | lecture |
| 6 | Promotion non enregistrée dans `play_stack` → casse l'en passant suivant et tout historique. | lecture |
| 7 | `README.md` est encodé en **UTF-16 LE + CRLF** : GitHub l'affiche illisible. | vérifié |

Les points 1-3 disparaissent d'eux-mêmes avec le générateur de coups légaux
(§4). Ils ne sont pas à corriger un par un.

---

## 4. Architecture cible

### 4.1 Le noyau

Le changement central : passer de « valider un coup proposé » à
« générer les coups légaux », dans un module pur, sans I/O.

```
Position                       # valeur, pas d'état mutable partagé
  ├── board, side_to_move, castling_rights, en_passant_square,
  │   halfmove_clock, fullmove_number
  ├── legal_moves() -> list[Move]
  ├── apply(move) -> Position          # renvoie une nouvelle position
  ├── to_fen() / from_fen()
  └── status() -> ongoing | checkmate | stalemate | fifty_move
                  | repetition | insufficient_material

Game
  ├── initial_fen, moves: list[MoveRecord]     # append-only
  ├── position_at(ply)                         # le rewind est dérivé
  └── clock state
```

`apply()` qui renvoie une nouvelle `Position` (au lieu de muter puis
`deepcopy(Board)`) rend le rewind, l'IA et les tests triviaux — et c'est
nettement plus rapide qu'un `deepcopy` par nœud d'arbre.

`legal_moves()` = coups pseudo-légaux + filtre « mon roi n'est pas en échec
après ». Une fois ce filtre posé :

- mat = en échec **et** `legal_moves()` vide
- pat = pas en échec **et** `legal_moves()` vide
- clouages, king-shadow, échec double : réglés d'office
- `is_it_checkmate` et sa logique « peut-on bloquer / manger ? » disparaissent
  (~60 lignes en moins), ainsi que la moitié de `move_utility.py`

### 4.2 Prouver que les règles sont justes : perft

`perft(n)` compte les nœuds à profondeur `n` depuis une position. On compare à
des valeurs publiées sur 5 positions de référence (startpos, Kiwipete,
positions 3/4/5). **Si perft(4) passe sur les 5, toutes les règles sont bonnes**
— roque, en passant, promotion, clouages, échecs découverts inclus. Un seul
test qui en vaut deux cents.

En complément : `python-chess` comme **oracle de test uniquement** (générer des
milliers de positions aléatoires, comparer les listes de coups légaux). Aucune
dépendance en production, confiance maximale.

### 4.3 Stack applicative

**Backend** — FastAPI + Pydantic (le moteur est déjà en Python).

- REST pour les actions : créer une partie, jouer un coup, lister les coups
  légaux, importer un PGN, abandonner, proposer nulle
- WebSocket pour l'horloge et le push d'état
- **Serveur autoritaire** sur l'état, même en 1v1 local : cela évite de
  dupliquer les règles en JavaScript
- SQLite + SQLAlchemy pour persister (sinon un redémarrage perd la partie)

**Frontend** — React + TypeScript + Vite.

- Échiquier : `react-chessboard` piloté par FEN (rendu seul, la logique reste
  serveur), ou composant maison en CSS grid pour tout contrôler
- TanStack Query pour l'état serveur, petit store (Zustand) pour l'état UI
- Le client ne calcule **jamais** la légalité : il demande
  `GET /games/{id}/legal-moves?from=e2` et affiche les pastilles

### 4.4 L'horloge — le détail qui compte

Ne **jamais** décrémenter côté serveur à chaque tick. Stocker
`{white_ms, black_ms, turn_started_at}` et calculer à la lecture. Le client
interpole localement (~100 ms) pour la fluidité et se resynchronise à chaque
message serveur. Le flag-fall est constaté par le serveur, jamais par le client.

Prévoir l'incrément Fischer (`base + increment`) dès le modèle de données :
c'est gratuit maintenant, coûteux à rétro-ajouter.

Cas de règle associé : flag-fall alors que l'adversaire n'a pas le matériel
pour mater = nulle, pas victoire.

### 4.5 Le rewind — le modèle

L'historique est **append-only**. Le curseur de lecture (`viewing_ply`) est un
état **client**, pas serveur : regarder le coup 12 ne provoque aucun appel
réseau, c'est `position_at(12)` (ou une liste de FEN pré-calculée renvoyée avec
la partie). Rien n'est jamais annulé.

Si un joueur tente un coup alors que le curseur est dans le passé :
- **phase 3** : on le ramène au présent (simple, sans surprise)
- **phase 6** : on ouvre une **variante** — c'est ce que suggère le champ
  `explored_history` déjà présent dans `Board`

À distinguer du **takeback** (annuler réellement un coup, mode décontracté),
qui est une autre feature.

### 4.6 L'IA

Interface unique : `Engine.choose_move(position, level) -> Move`, deux
implémentations derrière.

1. **Maison** : minimax + élagage alpha-bêta + tri des coups + quiescence +
   évaluation matériel/PST. ~300 lignes, profondeur 3-4 jouable en Python pur
   si `apply()` ne fait pas de `deepcopy`. C'est l'option pédagogique.
2. **Stockfish** en sous-processus UCI : fort, ~50 lignes, mais binaire externe
   à installer.

Stockfish sert aussi à l'analyse a posteriori — ce que le nom du dépôt promet.

### 4.7 Import / export

Deux formats : **FEN** (position) et **PGN** (partie complète).

Le parser SAN se code naturellement *par-dessus* `legal_moves()` : pour `Nf3`,
on filtre les coups légaux dont la pièce est un cavalier et l'arrivée `f3` ;
s'il en reste exactement un, c'est celui-là. La désambiguïsation (`Nbd2`,
`R1e2`) tombe du même mécanisme, et l'export PGN vient avec. Donc :
`legal_moves()` d'abord, PGN presque gratuit ensuite.

---

## 5. Découpage en phases

### Phase 0 — Assainir (1-2 j)
- `pyproject.toml`, package `chess_engine`, imports relatifs, layout `src/`
- CI GitHub Actions : tests + lint (ruff)
- Renommer `horse` → `knight` partout
- Réécrire `README.md` en UTF-8 (les notes de travail actuelles → `docs/`)

### Phase 1 — Noyau de règles (4-6 j) — *le gros morceau*
- `Position` immutable + FEN in/out
- `legal_moves()` complet : roque, en passant, promotion (4 pièces)
- Nulles : 50 coups, répétition triple (clé = FEN sans les compteurs),
  matériel insuffisant
- `status()` unifié ; mat et pat deviennent des cas dérivés
- **Perft 1-5 sur 5 positions de référence** + oracle `python-chess` en test
- Les 51 tests existants réécrits sur la nouvelle API

### Phase 2 — API (2-3 j)
- `POST /games`, `GET /games/{id}`, `POST /games/{id}/moves`,
  `GET /games/{id}/legal-moves`, `/resign`, `/draw-offer`
- Horloge serveur-autoritaire + WebSocket
- SQLite
- Tests d'API

### Phase 3 — Front 1v1 local (4-6 j)
- Échiquier : drag & drop **et** clic-clic, pastilles de coups légaux,
  surbrillance du dernier coup et de l'échec
- Dialogue de promotion
- Liste des coups en SAN + navigation clavier (←/→/Home/End) = **le rewind**
- Double horloge, retournement du plateau, abandon / nulle
- Écran de fin de partie avec le résultat (1-0 / 0-1 / ½-½)

### Phase 4 — Import / export (2-3 j)
- Parser et écrire le PGN, charger une FEN
- Coller un PGN ou charger un fichier
- Mode « revoir une partie importée » : réutilise le composant rewind tel quel

### Phase 5 — IA (3-5 j)
- Interface `Engine`, minimax alpha-bêta, niveaux (profondeur ou temps)
- Exécution hors du thread de requête pour ne pas bloquer l'API
- Option Stockfish UCI derrière la même interface

### Phase 6 — Analyse (le nom du dépôt)
- Évaluation par coup, barre d'éval, détection gaffe / erreur / imprécision
- Meilleur coup suggéré, flèches
- Variantes dans le rewind

---

## 6. Ajouts recommandés à la liste initiale

Par ordre de rapport valeur / effort :

1. **Abandon + proposition de nulle + résultat de partie** — sans ça, une partie
   ne se termine jamais proprement
2. **FEN/PGN comme format pivot** dès le départ — ce n'est pas une feature,
   c'est une fondation
3. **Perft** — le seul moyen d'avoir vraiment confiance dans les règles
4. **Incrément Fischer** — gratuit si prévu dès le modèle de données
5. **Persistance SQLite** — sinon un `uvicorn --reload` perd la partie en cours
6. **Variantes dans le rewind** — ce qui transforme le rewind en outil d'analyse
7. **Nommage d'ouverture (ECO)** — petite table, gros effet perçu
8. Sons, thèmes de pièces, annotations (flèches / cases en clic droit),
   accessibilité clavier, export PNG/GIF de la partie

### Explicitement hors périmètre pour l'instant
Multijoueur en ligne (auth, matchmaking, anti-triche : c'est un autre projet),
comptes utilisateurs, classement Elo.

---

## 7. Décisions ouvertes

1. **Moteur maison ou `python-chess` ?** Recommandation : garder le moteur
   maison (c'est l'intérêt du projet) et n'utiliser `python-chess` qu'en
   oracle de test.
2. **IA maison ou Stockfish ?** Recommandation : l'interface d'abord, minimax
   maison ensuite (c'est là qu'est l'apprentissage), Stockfish en option.
3. **Refonte du noyau ou correctifs incrémentaux ?** Recommandation : refonte.
   Les bugs 1-3 du §3 et les blocages 1/3/4 du §2 ont la même cause racine ;
   les corriger un par un coûte plus cher que de poser `legal_moves()`.

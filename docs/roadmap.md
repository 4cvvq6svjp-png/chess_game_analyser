# Roadmap — de moteur terminal à jeu d'échecs complet (React + API)

Document de planification. État des lieux du code existant, blocages
structurels identifiés, architecture cible et découpage en phases.

Compagnon de [`code-review-2026-06.md`](./code-review-2026-06.md) (bugs déjà
corrigés) et [`chess-logic-todo.md`](./chess-logic-todo.md) (dette de règles).

---

## 1. État des lieux

~1 380 lignes de Python, stdlib uniquement, zéro dépendance de production, jeu
jouable au terminal. 51 tests `unittest`, tous verts.

### Architecture actuelle

Modules du package `chess_engine` (`src/chess_engine/`, installé en editable).

| Module | Rôle |
|---|---|
| `pieces.py` | `Piece` (ABC) : `_is_valid_move`, `_move_piece(add\|remove)`, `_can_move`, `_execute_move` |
| `pawn/knight/bishop/rook/queen/king.py` | une classe par pièce, valident un coup **proposé** |
| `move_utility.py` | ray-walking statique : `check_diags/lines/knights`, `reach_sqr_*` |
| `chess_board.py` | matrice 8×8 `list[list[Piece\|None]]`, `play_stack`, détection échec/mat/pat, affichage |
| `chess_game.py` | boucle de jeu, parsing `"a1/a3"`, rejet de l'auto-échec par `deepcopy` |
| `player.py` | `input()` terminal |

Convention de coordonnées : `board[row][col]`, `row 0` = rang 8, `col 0` = colonne a.

### Conventions surprenantes à connaître avant de toucher au code

- Les `check_*` renvoient `{"check": False}` quand la case **est** attaquée. Le
  booléen est inversé par rapport à son nom.
- `is_in_check` compte les `True` : 3 = pas d'échec, ≤ 1 = échec double.
- ~~Le cavalier porte le nom `"horse"`~~ → corrigé en phase 0 : `"knight"`
  partout, ce qui règle du même coup la promotion en cavalier.
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
5. ~~**Imports plats**~~ → **levé en phase 0**. Le moteur est le package
   `chess_engine` (layout `src/`, imports relatifs, `pip install -e .`) :
   importable depuis n'importe où, donc consommable par un serveur web.

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
| 7 | ~~`README.md` encodé en **UTF-16 LE + CRLF**~~ : il bloquait aussi `pip install` (setuptools lit le readme en UTF-8). | **corrigé** (phase 0) |

Les points 1-3 disparaissent d'eux-mêmes avec le générateur de coups légaux
(§4). Ils ne sont pas à corriger un par un.

---

## 4. Architecture cible

### 4.0 Pourquoi un générateur de coups, et pas seulement un validateur

Valider un coup au moment de l'envoi est le chemin le moins cher quand la
question est « le joueur propose e2e4, est-ce légal ? ». C'est ce que fait le
code actuel, et il le fait bien. Le problème n'est pas le coût : c'est que
**toutes les features visées posent la question dans l'autre sens**.

| Feature | Question réellement posée |
|---|---|
| Pastilles sur l'échiquier | « Je clique ce cavalier : quelles cases s'allument ? » |
| Mat / pat | « L'adversaire a-t-il **zéro** coup légal ? » |
| IA minimax | « Quels coups explorer à ce nœud ? » |
| Import PGN (`Nf3`) | « Quel cavalier peut aller en f3 ? » |

**L'échiquier.** Avec un simple validateur, le front devrait demander « et a1 ?
et a2 ? … » — 64 questions par clic. On finit par écrire un endpoint qui répond
« voici la liste » : c'est un générateur, écrit sans le dire.

**Le mat.** « Est-ce mat ? » signifie « l'adversaire n'a aucun coup légal » :
une question d'énumération par nature. `is_it_checkmate` la contourne en
raisonnant par cas (le roi peut-il fuir ? manger l'attaquant ? s'interposer ?)
et les trois bugs du §3 sont exactement dans ces trois cas. Avec un générateur,
`mat = en_échec and not legal_moves()` : plus de cas particulier à oublier.

**L'IA.** Minimax a besoin de la liste des coups à chaque nœud. Sans
générateur, il n'y a pas de point d'entrée du tout.

**Le PGN.** `Nf3` ne dit pas d'où vient le cavalier ; on le retrouve en
filtrant les coups légaux. Le parser SAN se pose par-dessus en ~30 lignes.

### Le coût est plus faible que celui payé aujourd'hui

Une position typique a 30-40 coups légaux. Générer la liste = produire les ~40
candidats géométriques puis tester pour chacun « mon roi est-il en échec
après ? ». Ce test par candidat est **exactement** ce que `launch_game` fait
déjà à chaque coup joué (`deepcopy` + `is_in_check`). Générer tous les coups
coûte donc ~40 fois un coup validé : bien moins d'une milliseconde.

Et le code **énumère déjà**, de façon incomplète : `_is_pat` parcourt les 64
cases et essaie 8 directions par pièce ; `is_it_checkmate` scanne les 8 cases
autour du roi puis toutes les cases d'interposition. Le générateur n'ajoute pas
de calcul, il remplace trois demi-énumérations éparpillées et boguées par une
seule, correcte.

Le vrai enjeu de performance est ailleurs : remplacer `deepcopy(Board)` par une
copie légère (ou un make/unmake). Invisible pour un coup humain ; décisif pour
le minimax en profondeur 4 (~40⁴ ≈ 2,5 M de nœuds), où c'est la différence
entre plusieurs minutes et quelques secondes par coup.

Le validateur ne disparaît pas : `is_legal(move) = move in
position.legal_moves()`. Le chemin « le joueur envoie un coup » reste une ligne.

### La bibliothèque de pièces est conservée

| Fichier | Sort |
|---|---|
| `pieces.py`, `pawn/knight/bishop/rook/queen/king.py` | **gardés**, une méthode change de forme |
| `move_utility.py` | ray-walking réutilisé ; les `reach_sqr_*` (~60 l.) deviennent inutiles |
| `chess_board.py` | `is_it_checkmate` supprimé, `_is_pat` réduit à une ligne |
| `chess_game.py` | scindé : objet de partie pur + adaptateur CLI |
| `tests/` | gardés, réécrits sur la nouvelle signature |

```python
# avant
class Knight(Piece):
    def _is_valid_move(self, square_from, square_to, board) -> bool: ...

# après
class Knight(Piece):
    def pseudo_moves(self, position, square) -> Iterator[Move]: ...
```

Même hiérarchie, mêmes fichiers : chaque pièce continue de connaître sa propre
géométrie. Elle *produit* ses destinations au lieu d'en *juger* une. Le filtre
« ça laisse-t-il mon roi en échec ? » est écrit **une seule fois**, sur
`Position`, au lieu d'être oublié à trois endroits.

Les droits de roque vont sur `Position` (comme dans la FEN), pas sur les
pièces : les classes restent sans état, et le blocage n° 4 du §2 (identité de
la pièce perdue à chaque coup) s'évapore au lieu d'être à corriger.

### Migration incrémentale, pas big-bang

1. Ajouter `pseudo_moves()` à chaque classe **à côté** de `_is_valid_move` —
   rien ne casse, les 51 tests restent verts
2. Ajouter `Position.legal_moves()` qui agrège et filtre
3. Brancher **perft** → on voit immédiatement si les règles sont bonnes
4. Réécrire `is_it_checkmate` / `_is_pat` par-dessus → les trois bugs tombent
5. Ajouter roque, FEN, nulles
6. Supprimer `_is_valid_move` et `reach_sqr_*` quand plus rien ne les appelle

À chaque étape, le jeu terminal reste jouable.

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

### 4.2 bis — Parties réelles rejouées : le test d'intégration

Perft et l'oracle valident les règles *localement* : à une position donnée, la
liste des coups est-elle la bonne ? Ils ne disent rien de la **chaîne complète**
— lire une partie, la rejouer coup après coup, et reconnaître son issue.

D'où un troisième filet, complémentaire : un corpus de **parties connues à
issue déterministe**, rejouées de bout en bout par le moteur.

Le test, pour chaque partie du corpus :

1. charger le PGN et partir de la position initiale
2. rejouer **chaque** coup — aucun ne doit être refusé par `legal_moves()`
3. vérifier qu'à la fin, `status()` correspond au résultat enregistré
   (mat, pat, nulle par répétition / 50 coups / matériel insuffisant)
4. vérifier qu'aucun **faux positif** ne se déclenche en cours de route : pas de
   mat ni de pat annoncé avant le dernier coup

Un seul coup légal refusé, un mat annoncé trop tôt, et le test tombe en
désignant la partie et le numéro du coup — c'est un localisateur de bug, pas
seulement un détecteur.

**Ce que ça attrape et que perft rate.** Perft compte des nœuds ; il ne
traverse jamais le parser, ni `status()`, ni l'historique. Une régression dans
la lecture SAN, dans la tenue de `play_stack` (cf. bug n° 6 : promotion non
enregistrée), ou un pat détecté un demi-coup trop tôt passent inaperçus en
perft et sautent immédiatement ici. Inversement, ce corpus ne prouve rien sur
les positions exotiques — d'où la complémentarité.

**Corpus.** Une dizaine de parties suffit, choisies pour leur couverture plutôt
que pour leur célébrité :

| Partie | Ce qu'elle couvre |
|---|---|
| Morphy — Duke of Brunswick & Comte Isouard, 1858 | mat, sacrifices, petit roque |
| Anderssen — Kieseritzky, 1851 (« Immortelle ») | mat, série de prises |
| Kasparov — Topalov, 1999 | partie longue, roi baladeur |
| une partie à promotion (dame **et** sous-promotion) | promotion, bug n° 6 |
| une partie avec prise en passant | en passant dans un vrai contexte |
| une nulle par répétition | répétition triple |
| une nulle par la règle des 50 coups | compteur de demi-coups |
| une finale R+F vs R | matériel insuffisant |
| un pat classique en finale | pat vs mat |
| grand roque des deux côtés | roque long |

**Provenance et reproductibilité.** Les coups d'une partie sont des faits, pas
une œuvre : pas de difficulté de licence. La base ouverte de Lichess (CC0) ou
un export PGN public font l'affaire.

Point important : les fichiers sont **téléchargés une fois puis versionnés**
dans `tests/data/`, jamais récupérés au moment du test. Une CI qui dépend du
réseau est une CI qui rougit sans raison — et un corpus figé rend les échecs
reproductibles.

**Quand.** Le test a besoin de lire du SAN (`Nf3`), ce qui suppose
`legal_moves()` (§4.7). Deux options :

- **fin de phase 1** : rejouer les parties en notation de coordonnées
  (`e2e4`), obtenue en convertissant le corpus une fois pour toutes. Le filet
  est en place au plus tôt, sans attendre le parser.
- **phase 4** : rejouer le PGN directement, ce qui teste *aussi* le parser.

Les deux se cumulent : la version coordonnées valide le moteur, la version PGN
valide l'import. La première est la plus rentable, et c'est celle à écrire
d'abord.

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

1. **Maison — retenu en premier** : minimax + élagage alpha-bêta + tri des
   coups + quiescence + évaluation matériel/PST. ~300 lignes, profondeur 3-4
   jouable en Python pur **à condition que `apply()` ne fasse pas de
   `deepcopy`** (§4.0) — c'est la contrainte de perf qui compte vraiment ici.
2. **Stockfish** en sous-processus UCI : fort, ~50 lignes, binaire externe à
   installer. Branché plus tard derrière la même interface, surtout pour la
   phase analyse.

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

### Phase 0 — Assainir ✅ *terminée*
- ✅ `pyproject.toml`, package `chess_engine`, imports relatifs, layout `src/`
  (`pip install -e .`, script `chess-game`, plus de `sys.path` dans les tests)
- ✅ CI GitHub Actions : tests + lint (ruff) sur Python 3.10 et 3.12
- ✅ Renommer `horse` → `knight` partout — corrige au passage la promotion en
  cavalier, `create_piece_by_name` attendant déjà `"knight"`
- ✅ Réécrire `README.md` en UTF-8 ; notes de travail → `docs/journal-de-bord.md`

Les 51 tests restent verts, le jeu terminal reste jouable. Aucun changement de
règles.

### Phase 1 — Noyau de règles (4-6 j) — *le gros morceau*

Suit l'ordre de migration incrémentale du §4.0 : à chaque étape les tests
restent verts et le jeu terminal jouable.

- `pseudo_moves()` ajouté à chaque classe de pièce, à côté de `_is_valid_move`
- `Position` immutable + FEN in/out
- `legal_moves()` complet : roque, en passant, promotion (4 pièces)
- Nulles : 50 coups, répétition triple (clé = FEN sans les compteurs),
  matériel insuffisant
- `status()` unifié ; mat et pat deviennent des cas dérivés
- **Perft 1-5 sur 5 positions de référence** + oracle `python-chess` en test
- **Corpus de parties réelles rejouées** (§4.2 bis), en notation de
  coordonnées, avec les PGN versionnés dans `tests/data/`
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
- Rejouer le corpus de parties **depuis le PGN** cette fois (§4.2 bis) : le même
  test valide alors le parser en plus du moteur
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
3 bis. **Corpus de parties rejouées** (§4.2 bis) — le pendant « bout en bout »
   de perft : couvre le parser, `status()` et l'historique, que perft ne
   traverse jamais
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

## 7. Décisions prises

| Sujet | Décision |
|---|---|
| **Noyau de règles** | Générateur `legal_moves()` (§4.0), migré **incrémentalement**. La bibliothèque de classes de pièces est conservée : chaque classe garde sa géométrie, elle produit ses destinations au lieu d'en juger une. |
| **Bibliothèque externe** | Moteur maison. `python-chess` **uniquement en oracle de test** (comparaison de listes de coups légaux), jamais en dépendance de production. |
| **IA** | Minimax maison en premier : alpha-bêta, tri des coups, quiescence, éval matériel/PST. Stockfish reste branchable plus tard derrière la même interface `Engine.choose_move()`, notamment pour la phase analyse. |
| **Architecture** | Serveur FastAPI **autoritaire** sur les règles, y compris en 1v1 local. Le front ne calcule jamais la légalité : il demande les coups légaux à l'API. Une seule implémentation des règles, et le backend est de toute façon nécessaire pour l'IA et l'analyse. |
| **Stratégie de test** | Trois filets complémentaires : **perft** (exhaustivité combinatoire), **oracle `python-chess`** (comparaison de listes sur positions aléatoires) et **corpus de parties réelles rejouées** de bout en bout (§4.2 bis). Corpus PGN versionné dans `tests/data/`, jamais téléchargé pendant le test. |

### Reste à trancher plus tard
- Rewind : ramener au présent (phase 3) puis variantes (phase 6) — confirmé au
  moment de la phase 3.
- Échiquier `react-chessboard` piloté par FEN, ou composant maison en CSS grid.
- Cadences proposées par défaut (3+2, 5+0, 10+0, 15+10…).

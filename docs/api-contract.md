# Contrat d'API — phase 2

**Statut : implémenté en mémoire (tranche 2.2, paquet `chess_api`) ; SQLite (2.3) et horloge (2.4) à venir.** Ce document fixe la forme avant
d'écrire la moindre ligne de FastAPI. Il complète le [roadmap](./roadmap.md),
dont la §5 découpe la phase 2 en cinq tranches.

Relu à l'aune des phases 3 à 6 : le document réserve dès maintenant ce dont
l'IA (`players`), l'horloge (`time_control`) et la liste des coups (`san`)
auront besoin, pour ne pas changer de forme quand le front en dépendra.

---

## 1. Trois principes qui décident presque tout

**Le serveur est autoritaire, le client n'a pas de moteur.** C'est la décision
d'architecture du roadmap (§7), et elle a une conséquence qu'on oublie
facilement : le client ne peut *rien* dériver. Ni les coups légaux, ni « suis-je
en échec », ni la position au coup 12. Tout ce que le front affiche doit être
servi.

**Le registre est append-only.** On ajoute des coups, on ne remplace jamais un
plateau. Donc pas de `PUT /games/{id}`, pas de suppression de coup. Un
*takeback* sera une nouvelle partie plus courte, pas une mutation.

**La FEN est le format pivot, l'UCI la notation des coups.** `str(Move)` produit
déjà `"e2e4"` et `"e7e8q"` : la promotion est le suffixe, donc pas de champ
séparé. C'est aussi ce que Stockfish parlera en phase 5.

---

## 2. Prérequis dans le moteur : des exceptions typées ✅

L'API doit distinguer « ce coup n'est pas légal » (422) de « la partie est
finie » (409) : réactions client différentes. Les séparer en lisant le texte
français du message n'est pas un contrat, c'est un piège. `Game` levait un
`ValueError` nu pour cinq conditions distinctes ; chaque raison a désormais
son type (`chess_engine/errors.py`) :

```python
class ChessError(ValueError): ...                 # tous les refus du moteur
class IllegalMove(ChessError):  move: str         # → 422 illegal_move
class GameOver(ChessError):     status: Status    # → 409 game_over
class UnknownColor(ChessError): color             # → 422
class InvalidFen(ChessError):   fen, reason       # → 422 invalid_fen
```

- **`ChessError` hérite de `ValueError`.** Chacun signale bien une valeur
  refusée, et le code qui attrapait déjà `ValueError` — le terminal — continue
  de marcher sans connaître ces types.
- **`GameOver` passe avant `IllegalMove`.** Après un mat il n'existe plus aucun
  coup légal : chercher le coup d'abord répondait « illégal » là où la raison
  est « partie terminée ». `play` et `play_text` vérifient donc la fin de
  partie en premier.
- **`InvalidFen` couvre aussi ce qui échoue en dessous** du parseur — un
  compteur qui n'est pas un nombre, une case d'en passant hors échiquier. C'est
  ce qui permet à `POST /games` de répondre `invalid_fen` sans rien savoir des
  détails de lecture.

### 2 bis. Et l'écriture du SAN

Le front de la phase 3 affiche la liste des coups en notation algébrique
(`Nf3`, `exd5`, `O-O`, `Qxf7#`). Sans moteur, il ne peut pas la produire à
partir de `g1f3` : il lui faut savoir qu'une pièce est un cavalier, si un autre
cavalier atteint la même case, si le coup donne échec ou mat. Le SAN doit donc
être **servi**, et son écriture remonte de la phase 4 à la phase 2.

Seule l'**écriture** remonte. Elle se code sur `legal_moves()` : la pièce qui
part, la désambiguïsation par les autres coups légaux de même pièce vers la
même case, le suffixe `+`/`#` par `apply()` puis `status()`. La **lecture** du
SAN — le parser PGN — reste en phase 4.

```python
GamePosition.san(move: Move) -> str      # "Nbd2", "exd6", "e8=Q+", "O-O-O"
```

`Game` calcule le SAN de chaque coup une fois, au moment où il est joué, comme
il le fait déjà pour les clés de répétition.

---

## 3. L'identifiant de partie est un justificatif d'accès

Le point qui décide du reste. **Il n'y a pas d'authentification** : quiconque
connaît l'id peut jouer les deux camps et abandonner. L'id *est* le mot de
passe — le modèle « toute personne disposant du lien ».

Il doit donc être **imprédictible**. Un entier auto-incrémenté laisserait
n'importe qui énumérer les parties en cours et abandonner à la place des
joueurs. Ce n'est pas un raffinement, c'est la seule protection existante.

```python
import secrets
game_id = secrets.token_urlsafe(8)      # "kJ3v_8xQp2A", 64 bits
```

`secrets` et non `random` : la distinction entre « un nombre quelconque » et
« un nombre que personne ne devine ».

- **Créé côté serveur uniquement.** Jamais fourni par le client, qui pourrait en
  choisir un devinable ou entrant en collision.
- **Contrainte d'unicité au stockage.** Non parce qu'une collision est plausible
  sur 64 bits, mais parce qu'un id dupliqué mélangerait silencieusement deux
  parties. En cas de collision : retirer, ne pas réutiliser.
- **Limite connue** : l'id circule dans les URL, donc dans les journaux serveur
  et l'historique du navigateur. Acceptable ici — à savoir, pas à découvrir.

**Évolution prévue** : pour distinguer joueurs et spectateurs, l'id de partie
devient public (lecture seule) et un **jeton par camp** s'ajoute pour jouer.
Aucun changement de forme dans les payloads, un en-tête en plus.

---

## 4. Les endpoints

```
POST   /api/v1/games                  créer
GET    /api/v1/games/{id}             l'état complet
POST   /api/v1/games/{id}/moves       jouer
POST   /api/v1/games/{id}/resign      abandonner
```

Quatre, et c'est volontaire. Le roadmap prévoyait un
`GET /legal-moves?from=e2` : **écarté**. Les coups sont des chaînes UCI, donc
filtrer ceux qui partent de e2 est un `startswith` côté client sur une liste de
quarante éléments déjà reçue. Un aller-retour réseau par clic de pièce pour
économiser un `filter()` est un mauvais échange.

### POST /games

```json
{
  "initial_fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "auto_draw": true,
  "players": {"w": "human", "b": "human"},
  "time_control": {"base_ms": 180000, "increment_ms": 2000}
}
```

Tous les champs sont facultatifs. Par défaut : position initiale, nulles
automatiques, deux humains, pas d'horloge (`time_control: null`).

```
1. GamePosition.from_fen(initial_fen)   → InvalidFen = 422, rien n'est créé
2. players, time_control valides        → sinon 422, rien n'est créé
3. game = Game(initial_fen=…, auto_draw=…)
4. id = secrets.token_urlsafe(8)
5. store.create(id, GameRecord(game, players, time_control))
6. si le camp au trait est un moteur    → sa réflexion démarre (§4 bis)
7. 201 + en-tête Location + le document
```

**`players` et `time_control` sont réservés dès maintenant**, bien que ni l'IA
(phase 5) ni l'horloge (tranche 2.4) n'existent encore. Même raisonnement que
pour l'incrément Fischer : un champ prévu à la création ne coûte rien, un
champ ajouté quand un front en dépend déjà oblige à gérer des parties créées
sans lui. D'ici là, un `players` contenant un moteur est refusé en 422
(`unsupported_player`), et `time_control` est accepté mais `clock` vaut `null`
jusqu'à la tranche 2.4.

**Validation de `time_control`** : `base_ms > 0`, `increment_ms >= 0`. Pas de
liste fermée de cadences : les cadences proposées par défaut (3+2, 10+0…) sont
une affaire de front.

**Ni l'un ni l'autre ne vont dans `Game`.** `Game` est une partie d'échecs :
une position de départ et des coups. Qui tient quel camp est une information
d'application, que le store range à côté — d'où le `GameRecord`. L'horloge,
elle, produit une fin de partie (la chute du drapeau) et se raccorde à `Game`
par un `Termination`, exactement comme l'abandon.

### GET /games/{id}

```
1. store.get(id)                        → absent = 404
2. document(game)
3. 200
```

### POST /games/{id}/moves

Le seul endpoint qui fait avancer l'histoire.

```
1. store.get(id)                        → 404
2. expected_ply != game.ply             → 409 stale_ply + le document
3. le camp au trait est un moteur       → 409 not_your_turn + le document
4. horloge : le drapeau est-il tombé ?  → oui = Termination, 409 game_over
5. game.play_text(move)
     IllegalMove                        → 422 illegal_move + le document
     GameOver                           → 409 game_over + le document
6. store.save(id, game)
7. si le camp au trait est un moteur    → sa réflexion démarre (§4 bis)
8. 200 + le document
```

L'étape 4 ne concerne que les parties avec horloge (tranche 2.4) : un coup qui
arrive après la chute du drapeau ne sauve pas la partie. Le même constat a lieu
à chaque `GET` — c'est la lecture qui découvre qu'une partie est perdue au
temps, puisque le serveur ne décompte jamais en continu (roadmap §4.4).

### POST /games/{id}/resign

**Sans `expected_ply`**, délibérément. Un abandon est valable à n'importe quel
demi-coup ; exiger un ply le ferait échouer si un coup adverse atterrissait
juste avant, alors que l'intention du joueur n'a pas changé. L'abandon est
inconditionnel — c'est le coup qui a besoin d'un garde-fou de concurrence.

```
1. store.get(id)                        → 404
2. game.resign(color)
     GameOver                           → 409
     UnknownColor                       → 422 unknown_color
3. store.save(id, game)
4. 200 + le document
```

---

## 4 bis. Quand un camp est tenu par le moteur *(phase 5)*

Rien à implémenter en phase 2 hormis le refus du §4, mais la forme doit être
fixée maintenant, parce qu'elle décide de ce que `POST /moves` renvoie.

```json
"players": {"w": "human", "b": {"engine": {"level": 3}}}
```

**`POST /moves` n'attend pas la réponse du moteur.** À profondeur 4, un coup
de minimax en Python pur se compte en secondes. Faire patienter la requête du
joueur jusque-là, c'est un spinner sans retour visuel sur son propre coup et
un délai d'expiration HTTP à surveiller. Donc :

1. le coup humain est joué et renvoyé tout de suite (200, `ply` avancé,
   `side_to_move` = le moteur) ;
2. la réflexion part hors du thread de requête ;
3. son coup est poussé par le WebSocket de la tranche 2.4 — ou, avant lui,
   retrouvé par un `GET` que le client répète tant que
   `players[side_to_move]` est un moteur.

Le client n'a pas besoin d'un champ « le moteur réfléchit » : `players` et
`side_to_move` le disent déjà.

**Le moteur passe par le même chemin que les humains**, `expected_ply`
compris. Si le joueur abandonne pendant la réflexion, le coup du moteur arrive
sur une partie terminée ou un ply périmé, et il est jeté. Pas de verrou, pas
d'annulation de tâche à orchestrer : la garde de concurrence du §6 suffit.

**`not_your_turn`** : sans authentification (§3), rien n'empêche un client de
poster un coup pour le camp du moteur. Le serveur le refuse — c'est la seule
règle d'accès que le contrat peut tenir sans identifier personne.

---

## 5. Le document de partie

```json
{
  "id": "kJ3v_8xQp2A",
  "ply": 3,
  "status": "ongoing",
  "result": null,

  "players": {"w": "human", "b": "human"},
  "time_control": {"base_ms": 180000, "increment_ms": 2000},

  "fen": "rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2",
  "side_to_move": "b",
  "in_check": false,
  "legal_moves": ["a7a6", "a7a5", "b8c6", "..."],

  "moves": ["e2e4", "e7e5", "g1f3"],
  "san": ["e4", "e5", "Nf3"],
  "positions": ["rnbqkbnr/pppppppp/...", "...", "...", "..."],

  "termination": null,
  "clock": null
}
```

**`in_check` et `legal_moves` sont servis** parce que le client ne peut pas les
calculer. Le front a besoin des coups légaux à *chaque* position pour ses
pastilles, donc autant les embarquer : quarante chaînes, ~300 octets. Ils
restent en UCI, pas en SAN : le front en a besoin pour savoir d'où part et où
arrive chaque coup, ce qu'un SAN ne dit pas (`Nf3` ne nomme pas sa case de
départ).

**`moves` et `san` sont parallèles** : `san[i]` est l'écriture humaine de
`moves[i]`. Le premier sert à la machine (surbrillance du dernier coup, envoi à
Stockfish), le second à l'affichage de la liste des coups (§2 bis). Pas de
`last_move` : c'est `moves[-1]`, et un champ dérivé de plus est un champ qui
peut mentir.

**`positions` contient une FEN par demi-coup**, `positions[0]` étant la position
initiale. C'est ce qui rend le rembobinage gratuit : le roadmap (§4.5) fait du
curseur un état **client**, sans appel réseau. Mais sans moteur, le client ne
peut pas rejouer les coups pour retrouver la position 12 — il faut donc la lui
donner. ~13 Ko pour une partie de 300 demi-coups. Si ça devient gênant,
`positions` passe derrière `GET /games/{id}/positions` ; pas d'emblée.

**`players` et `time_control`** sont renvoyés tels que fixés à la création
(§4). Le front en déduit qui joue en bas du plateau, quand il doit attendre le
moteur, et s'il affiche une horloge.

**`termination`** quand la partie s'est terminée hors de l'échiquier :

```json
"termination": {"status": "resignation", "by": "w", "at": 1727000000.0}
```

`by` est le camp qui a provoqué la fin : celui qui abandonne, celui dont le
drapeau tombe.

**`clock` vaut `null`** quand la partie n'a pas de `time_control`, et partout
jusqu'à la tranche 2.4. Sa forme est déjà décidée par le §4.4 du roadmap :

```json
"clock": {"white_ms": 180000, "black_ms": 174320, "running": "b", "as_of": 1727000000.123}
```

`as_of` est la référence temporelle **du serveur** : sans elle, le client
interpole depuis sa propre horloge, qui dérive.

### Les valeurs de `status`

La liste est fermée : le front doit savoir afficher chacune.

| Valeur | Fin de partie | `result` | Origine |
|---|---|---|---|
| `ongoing` | non | `null` | — |
| `checkmate` | oui | gain | la position |
| `stalemate` | oui | nulle | la position |
| `fifty_move` | oui | nulle | la position |
| `insufficient_material` | oui | nulle | la position |
| `repetition` | oui | nulle | l'historique |
| `resignation` | oui | gain | un `Termination` |
| `timeout` | oui | gain | un `Termination` *(tranche 2.4)* |
| `timeout_vs_insufficient_material` | oui | nulle | un `Termination` *(tranche 2.4)* |
| `agreement` | oui | nulle | un `Termination` *(reporté, §9)* |

**Pourquoi deux statuts pour la chute du drapeau.** La règle FIDE : perdre au
temps donne nulle si l'adversaire n'a *aucune* suite légale pour mater. Le
résultat ne se lit donc pas sur le seul statut `timeout`, or `Status.is_draw()`
ne regarde que le statut. Deux valeurs gardent cette propriété — et le front
peut expliquer pourquoi une chute de drapeau n'a pas fait de vainqueur.

Attention : ce n'est **pas** le test `insufficient_material` actuel, qui porte
sur les deux camps à la fois. Ici seul compte le matériel de celui qui n'est
*pas* tombé. Il faudra un test par camp dans `GamePosition`.

---

## 6. Concurrence : le ply fait office de version

```json
POST /api/v1/games/{id}/moves
{"move": "e2e4", "expected_ply": 3}
```

Le `ply` est déjà le numéro de version d'un journal append-only : significatif
pour le client, il survit à la sérialisation et n'a pas à être inventé. Un ETag
ferait le même travail en moins lisible.

Effet secondaire utile : rejouer la même requête échoue naturellement, puisque
le ply a avancé. Pas de double-coup possible.

**La garde n'est vraie que si « vérifier puis jouer » est atomique.** FastAPI
exécute les endpoints synchrones dans un pool de threads : deux coups postés
au même instant liraient le même `ply` et passeraient tous deux. Chaque
`GameRecord` porte donc un verrou, pris autour de la vérification *et* du coup.
Un test poste huit coups simultanés au même `expected_ply` : un seul passe.

---

## 7. Les erreurs rendent l'état

```json
409 {"error": "stale_ply", "expected_ply": 3, "actual_ply": 4, "game": {...}}
422 {"error": "illegal_move", "move": "e2e5", "game": {...}}
409 {"error": "game_over", "status": "resignation", "game": {...}}
409 {"error": "not_your_turn", "side_to_move": "b", "game": {...}}
422 {"error": "unknown_color", "color": "white", "game": {...}}
404 {"error": "game_not_found", "id": "..."}
422 {"error": "invalid_request", "detail": [...]}
422 {"error": "invalid_fen", "initial_fen": "...", "reason": "..."}
422 {"error": "unsupported_player", "color": "b"}
422 {"error": "invalid_time_control"}
```

Les trois derniers refusent une **création** : il n'y a pas encore de partie,
donc pas de `game` à rendre. Pas plus pour `game_not_found`, ni pour
`invalid_request` — un corps mal formé (champ manquant, mauvais type), que
FastAPI refuserait sinon dans son propre format : le remplacer donne à *tous*
les refus la même forme, un `error` lisible par la machine.

Le `game` complet dans **chaque** rejet : le client se resynchronise sans second
appel, ce qui est exactement ce dont il a besoin au moment où il vient de se
tromper.

Le code machine (`error`) est le contrat ; le message humain n'en fait pas
partie.

---

## 8. Le stockage, et ce que la mesure impose

```python
@dataclass
class GameRecord:
    game: Game
    players: dict[str, Player]            # {"w": "human", "b": ...}
    time_control: TimeControl | None
    clock: ClockState | None              # tranche 2.4

class GameStore(Protocol):
    def create(self, game_id: str, record: GameRecord) -> None: ...
    def get(self, game_id: str) -> GameRecord: ...
    def save(self, game_id: str, record: GameRecord) -> None: ...
```

Le store manipule un `GameRecord` et non un `Game` nu : `players`,
`time_control` et l'état de l'horloge sont des données d'application (§4), que
le moteur n'a pas à connaître mais que la base doit garder.

Définir cette frontière **dès la tranche 2.2** est ce qui permettra à SQLite
(2.3) de se substituer au dictionnaire sans qu'aucun endpoint bouge.

Mesuré sur la plus longue partie du corpus (303 demi-coups) :

| Opération | Coût |
|---|---|
| Reconstruire la partie depuis ses coups | **158 ms** |
| Projeter toutes les FEN, l'objet en main | 1,8 ms |
| Les coups en UCI | 1,2 Ko |
| Les FEN correspondantes | 13,3 Ko |

D'où la règle :

> **La base est le registre durable, pas le chemin de lecture.**

Le store garde les objets `Game` **vivants en mémoire** et écrit dans la base au
passage. Reconstruire à chaque `GET` mettrait 158 ms sur la requête la plus
fréquente de l'application. Au redémarrage, la reconstruction se fait
paresseusement au premier accès — 158 ms une fois, c'est acceptable.

On persiste les coups (1,2 Ko), on dérive les FEN (13,3 Ko).

Propriété agréable : reconstruire passe par `play_text`, donc **revalide toute
la partie**. Une ligne corrompue en base échoue bruyamment au lieu de servir une
position impossible.

---

## 9. Explicitement hors du contrat

**Un endpoint « coups légaux de cette FEN », sans partie.** Tentant, et utile en
phase 6 pour l'analyse. Mais l'ajouter maintenant invite le client à porter un
état que le serveur doit posséder — précisément la frontière que l'architecture
protège.

**L'authentification.** En 1v1 local, quiconque a l'id joue les deux camps, et
`POST /resign {"color": "w"}` dit simplement qui abandonne. Voir §3 pour
l'évolution.

**Les dépendances dans le moteur.** FastAPI, uvicorn et Pydantic vont dans un
extra `[api]`. `import chess_engine` doit continuer de fonctionner sans rien
installer d'autre.

**La proposition de nulle — reportée, pas abandonnée.** Le roadmap la prévoyait
en phase 2 (`/draw-offer`) ; elle sort du premier jet pour ne pas retarder le
reste. Ce qu'il faudra le moment venu : un état intermédiaire sur `Game`
(« w a proposé, b n'a pas répondu »), exposé dans le document sous la forme
`"draw_offer": null | "w" | "b"`, un statut `agreement` dans `Status`, et un
`Termination` avec `by: null` — la nulle acceptée est une décision commune.
Rien dans le contrat actuel ne s'y oppose : c'est un champ et un endpoint en
plus, aucun changement de forme.

---

## 10. Évolutions prévues, compatibles avec ce contrat

Rien à coder en phase 2. Ces lignes existent pour vérifier qu'aucune décision
d'aujourd'hui ne ferme une porte.

**Créer une partie à partir de coups** *(phase 4)*. `POST /games` acceptera un
champ `moves` (liste UCI), rejoué par `play_text` — c'est déjà le chemin de
reconstruction du store (§8), donc déjà testé. L'import PGN devient alors :
parser le PGN côté serveur, puis créer la partie avec `moves` et
`auto_draw: false`, pour suivre une partie d'archive où personne n'a réclamé la
nulle. Pas d'endpoint d'import dédié.

**Partir d'un coup d'une autre partie** *(phases 3 et 6)*. `POST /games` avec
`"from": {"game_id": "...", "ply": 12}` crée une **nouvelle** partie qui reprend
les douze premiers coups. C'est à la fois le *takeback* (principe du §1 : une
partie plus courte, pas une mutation) et la variante d'analyse. Le registre
reste append-only ; un lien de parenté entre parties suffira à les afficher en
arbre.

**L'analyse** *(phase 6)*. Une ressource à part, `GET /games/{id}/analysis`,
qui porte une évaluation par demi-coup. Elle ne s'ajoute pas au document de
partie : elle se calcule en tâche de fond, peut être partielle, et n'a pas la
même fréquence de mise à jour.


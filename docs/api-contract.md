# Contrat d'API — phase 2

**Statut : conçu, pas encore implémenté.** Ce document fixe la forme avant
d'écrire la moindre ligne de FastAPI. Il complète le [roadmap](./roadmap.md),
dont la §5 découpe la phase 2 en cinq tranches.

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

## 2. Prérequis dans le moteur : des exceptions typées

`Game` lève aujourd'hui un `ValueError` nu pour cinq conditions distinctes :

| Endroit | Condition |
|---|---|
| `play_text` | coup illégal ou mal écrit |
| `_play` | coup illégal dans cette position |
| `_play` | la partie est terminée |
| `resign` | couleur inconnue |
| `resign` | la partie est déjà terminée |

L'API doit distinguer « ce coup n'est pas légal » (422) de « la partie est
finie » (409) : réactions client différentes. Les séparer en lisant le texte
français du message n'est pas un contrat, c'est un piège.

À faire **avant** la couche web :

```python
class ChessError(Exception): ...
class IllegalMove(ChessError): ...
class GameOver(ChessError): ...
class UnknownColor(ChessError): ...
```

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

```
1. corps : initial_fen (facultatif), auto_draw (facultatif)
2. GamePosition.from_fen(initial_fen)   → ValueError = 422, rien n'est créé
3. game = Game(initial_fen=…, auto_draw=…)
4. id = secrets.token_urlsafe(8)
5. store.create(id, game)
6. 201 + en-tête Location + le document
```

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
3. game.play_text(move)
     IllegalMove                        → 422 illegal_move + le document
     GameOver                           → 409 game_over + le document
4. store.save(id, game)
5. 200 + le document
```

### POST /games/{id}/resign

**Sans `expected_ply`**, délibérément. Un abandon est valable à n'importe quel
demi-coup ; exiger un ply le ferait échouer si un coup adverse atterrissait
juste avant, alors que l'intention du joueur n'a pas changé. L'abandon est
inconditionnel — c'est le coup qui a besoin d'un garde-fou de concurrence.

```
1. store.get(id)                        → 404
2. game.resign(color)
     GameOver                           → 409
     UnknownColor                       → 422
3. store.save(id, game)
4. 200 + le document
```

---

## 5. Le document de partie

```json
{
  "id": "kJ3v_8xQp2A",
  "ply": 3,
  "status": "ongoing",
  "result": null,

  "fen": "rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2",
  "side_to_move": "b",
  "in_check": false,
  "legal_moves": ["a7a6", "a7a5", "b8c6", "..."],
  "last_move": "g1f3",

  "moves": ["e2e4", "e7e5", "g1f3"],
  "positions": ["rnbqkbnr/pppppppp/...", "...", "...", "..."],

  "termination": null,
  "clock": null
}
```

**`in_check` et `legal_moves` sont servis** parce que le client ne peut pas les
calculer. Le front a besoin des coups légaux à *chaque* position pour ses
pastilles, donc autant les embarquer : quarante chaînes, ~300 octets.

**`positions` contient une FEN par demi-coup**, `positions[0]` étant la position
initiale. C'est ce qui rend le rembobinage gratuit : le roadmap (§4.5) fait du
curseur un état **client**, sans appel réseau. Mais sans moteur, le client ne
peut pas rejouer les coups pour retrouver la position 12 — il faut donc la lui
donner. ~13 Ko pour une partie de 300 demi-coups. Si ça devient gênant,
`positions` passe derrière `GET /games/{id}/positions` ; pas d'emblée.

**`termination`** quand la partie s'est terminée hors de l'échiquier :

```json
"termination": {"status": "resignation", "by": "w", "at": 1727000000.0}
```

**`clock` existe et vaut `null`** jusqu'à la tranche 2.4. Sa forme est déjà
décidée par le §4.4 du roadmap :

```json
"clock": {"white_ms": 180000, "black_ms": 174320, "running": "b", "as_of": 1727000000.123}
```

`as_of` est la référence temporelle **du serveur** : sans elle, le client
interpole depuis sa propre horloge, qui dérive.

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

---

## 7. Les erreurs rendent l'état

```json
409 {"error": "stale_ply", "expected_ply": 3, "actual_ply": 4, "game": {...}}
422 {"error": "illegal_move", "move": "e2e5", "game": {...}}
409 {"error": "game_over", "status": "resignation", "game": {...}}
```

Le `game` complet dans **chaque** rejet : le client se resynchronise sans second
appel, ce qui est exactement ce dont il a besoin au moment où il vient de se
tromper.

Le code machine (`error`) est le contrat ; le message humain n'en fait pas
partie.

---

## 8. Le stockage, et ce que la mesure impose

```python
class GameStore(Protocol):
    def create(self, game_id: str, game: Game) -> None: ...
    def get(self, game_id: str) -> Game: ...
    def save(self, game_id: str, game: Game) -> None: ...
```

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

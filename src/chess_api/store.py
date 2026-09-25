"""Où vivent les parties : la frontière que SQLite viendra remplir (tranche 2.3).

Le store manipule un ``GameRecord`` plutôt qu'une ``Game`` nue : qui tient
quel camp, la cadence et l'horloge sont des données d'application, que le
moteur n'a pas à connaître mais que la base devra garder
(``docs/api-contract.md``, §8).

Aucune dépendance web ici : le store se teste seul, et l'implémentation en
mémoire ne sert pas qu'aux tests -- c'est elle qui gardera les parties
vivantes quand la base ne sera plus que le registre durable.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Protocol

from chess_engine import Game

#: Un joueur humain. Un moteur s'écrit ``{"engine": {"level": 3}}`` (phase 5).
HUMAN = "human"


@dataclass(frozen=True)
class TimeControl:
    """Une cadence : temps de base et incrément Fischer, en millisecondes."""

    base_ms: int
    increment_ms: int


@dataclass
class GameRecord:
    """Une partie et ce que l'application sait autour d'elle.

    ``lock`` sérialise les écritures sur *cette* partie. FastAPI exécute les
    endpoints synchrones dans un pool de threads : sans lui, deux coups postés
    au même instant liraient le même ``ply``, passeraient tous deux la garde
    ``expected_ply`` et seraient joués l'un après l'autre. Le verrou fait de
    « vérifier puis jouer » une seule opération -- c'est ce qui rend la garde
    du contrat (§6) réellement vraie.
    """

    game: Game
    players: dict[str, object] = field(default_factory=lambda: {"w": HUMAN, "b": HUMAN})
    time_control: TimeControl | None = None
    lock: threading.Lock = field(default_factory=threading.Lock, repr=False, compare=False)


class GameNotFound(KeyError):
    """Aucune partie sous cet identifiant."""


class DuplicateGameId(KeyError):
    """L'identifiant est déjà pris. L'appelant en tire un autre."""


class GameStore(Protocol):
    def create(self, game_id: str, record: GameRecord) -> None: ...
    def get(self, game_id: str) -> GameRecord: ...
    def save(self, game_id: str, record: GameRecord) -> None: ...


class InMemoryGameStore:
    """Un dictionnaire. Un redémarrage perd tout : c'est la tranche 2.3 qui y remédie.

    ``save`` n'a rien à faire ici -- le record *est* l'objet stocké, déjà
    modifié en place. Il est appelé quand même par les endpoints, parce que le
    store SQLite, lui, devra écrire : le contrat se tient dès maintenant.
    """

    def __init__(self):
        self._records: dict[str, GameRecord] = {}
        self._lock = threading.Lock()

    def create(self, game_id: str, record: GameRecord) -> None:
        with self._lock:
            if game_id in self._records:
                raise DuplicateGameId(game_id)
            self._records[game_id] = record

    def get(self, game_id: str) -> GameRecord:
        try:
            return self._records[game_id]
        except KeyError:
            raise GameNotFound(game_id) from None

    def save(self, game_id: str, record: GameRecord) -> None:
        if game_id not in self._records:
            raise GameNotFound(game_id)
        self._records[game_id] = record

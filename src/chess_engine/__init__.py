"""Moteur d'échecs : règles, positions et parties.

Point d'entrée public du paquet. Les modules internes s'importent entre eux
par imports relatifs ; les consommateurs (tests, API, IA) passent par ici :

    from chess_engine import Game, GamePosition

Le noyau tient en trois objets. ``GamePosition`` est l'état complet à un
instant -- les six champs d'une FEN -- et sait produire ses coups légaux.
``Move`` est un coup, une donnée inerte. ``Game`` est une position de départ
et une suite de coups, dont tout le reste se déduit.
"""

from .bishop import Bishop
from .document import game_document
from .game import Game, Termination
from .game_position import GamePosition, Status
from .king import King
from .knight import Knight
from .move import Move, square_from_name, square_name
from .move_utility import MoveUtility
from .pawn import Pawn
from .pieces import Piece
from .queen import Queen
from .rook import Rook

__all__ = [
    "Bishop",
    "Game",
    "Termination",
    "GamePosition",
    "King",
    "Knight",
    "Move",
    "MoveUtility",
    "Pawn",
    "Piece",
    "Queen",
    "Rook",
    "Status",
    "game_document",
    "square_from_name",
    "square_name",
]

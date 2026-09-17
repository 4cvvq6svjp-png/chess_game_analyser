"""Moteur d'échecs : règles, plateau et boucle de partie.

Point d'entrée public du package. Les modules internes s'importent entre eux
par imports relatifs ; les consommateurs (tests, API, IA) passent par ici :

    from chess_engine import Board, King, Pawn
"""

from .bishop import Bishop
from .chess_board import Board
from .chess_game import chess_game
from .game import Game
from .game_position import GamePosition, Status
from .king import King
from .knight import Knight
from .move import Move, square_from_name, square_name
from .move_utility import MoveUtility
from .pawn import Pawn
from .pieces import Piece
from .player import Player
from .queen import Queen
from .rook import Rook

__all__ = [
    "Bishop",
    "Board",
    "Game",
    "GamePosition",
    "King",
    "Knight",
    "Move",
    "MoveUtility",
    "Pawn",
    "Piece",
    "Player",
    "Queen",
    "Rook",
    "Status",
    "chess_game",
    "square_from_name",
    "square_name",
]

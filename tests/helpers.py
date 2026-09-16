"""Shared test helpers.

The engine is installed as the ``chess_engine`` package (``pip install -e .``),
so tests import it by name -- no ``sys.path`` juggling. Every test module pulls
the pieces/board through this helper.

Coordinate convention (matches the engine): board[row][col] with row 0 == rank 8
(top) and row 7 == rank 1; col 0 == file 'a'.
"""

from chess_engine import (
    Bishop,
    Board,
    GamePosition,
    King,
    Knight,
    Move,
    Pawn,
    Piece,
    Queen,
    Rook,
    chess_game,
    square_name,
)

__all__ = [
    "Bishop",
    "Board",
    "GamePosition",
    "King",
    "Knight",
    "Move",
    "Pawn",
    "Piece",
    "Queen",
    "Rook",
    "chess_game",
    "empty_board",
    "place",
    "square",
    "square_name",
]


def square(name):
    """``"e2"`` -> ``(6, 4)``. L'inverse de ``square_name``.

    Écrire les cases en notation d'échecs plutôt qu'en coordonnées rend les
    tests relisibles : ``square("e4")`` se vérifie d'un coup d'œil, ``(4, 4)``
    demande une conversion mentale à chaque lecture.
    """
    return (8 - int(name[1]), ord(name[0]) - ord("a"))


def empty_board():
    """A Board with an empty 8x8 grid and a fresh play stack."""
    b = Board("classic")
    b.chessboard = [[None for _ in range(8)] for _ in range(8)]
    b.play_stack = []
    return b


def place(board, piece, square):
    """Put ``piece`` on ``square`` (row, col) and return it."""
    board.chessboard[square[0]][square[1]] = piece
    return piece

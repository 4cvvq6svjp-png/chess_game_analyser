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
    King,
    Knight,
    Pawn,
    Piece,
    Queen,
    Rook,
    chess_game,
)

__all__ = [
    "Bishop",
    "Board",
    "King",
    "Knight",
    "Pawn",
    "Piece",
    "Queen",
    "Rook",
    "chess_game",
    "empty_board",
    "place",
]


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

"""Shared test helpers.

The game modules use flat imports (``from chess_board import Board``), so we add
``src/game_logic`` to ``sys.path`` here and let every test module import the
pieces/board through this helper.

Coordinate convention (matches the engine): board[row][col] with row 0 == rank 8
(top) and row 7 == rank 1; col 0 == file 'a'.
"""

import os
import sys

_SRC = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "src", "game_logic")
)
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from chess_board import Board          # noqa: E402
from chess_game import chess_game      # noqa: E402
from pieces import Piece               # noqa: E402
from pawn import Pawn                  # noqa: E402
from knight import Knight              # noqa: E402
from bishop import Bishop              # noqa: E402
from rook import Rook                  # noqa: E402
from queen import Queen                # noqa: E402
from king import King                  # noqa: E402


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

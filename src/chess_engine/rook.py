from typing import TYPE_CHECKING

from .move_utility import MoveUtility
from .pieces import ORTHOGONAL_DIRECTIONS, Piece

if TYPE_CHECKING:
    from collections.abc import Iterator

    from .chess_board import Board
    from .game_position import GamePosition
    from .move import Move


class Rook(Piece) :
    #: La tour ne connaît que les lignes et les colonnes.
    DIRECTIONS = ORTHOGONAL_DIRECTIONS

    def __init__(self, color) :
        super().__init__(color, "rook")


    def pseudo_moves(self, position: 'GamePosition', square: tuple) -> 'Iterator[Move]':
        """Produit les coups de la tour depuis ``square``, sans filtre de légalité.

        Le roque n'apparaît pas ici : il déplace deux pièces et dépend des
        droits portés par la position, donc il sera produit par
        ``GamePosition.legal_moves()``, pas par la tour.
        """
        return self._sliding_moves(position, square, self.DIRECTIONS)


    def _is_valid_move(self, square_from: tuple, square_to: tuple, board: 'Board'):
        return MoveUtility._is_line_valid(square_from, square_to, board.chessboard)
        


    def _move_piece(self, BOARD, square, add_or_remove):
        row, col = square
        # Change the board
        if add_or_remove == "add" :
            BOARD[row][col] = Rook(self.color)
        else :
            BOARD[row][col] = None
    

    def _can_move(self, board, square):
        ROW, COL = square
        for dr, dc in self.DIRECTIONS:
            if ROW+dr in range(8) and COL+dc in range(8) and self._is_valid_move(square, (ROW+dr, COL+dc), board):
                return True
        return False
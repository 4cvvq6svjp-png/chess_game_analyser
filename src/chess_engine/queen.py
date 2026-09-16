from typing import TYPE_CHECKING

from .move_utility import MoveUtility
from .pieces import ALL_DIRECTIONS, Piece

if TYPE_CHECKING:
    from collections.abc import Iterator

    from .chess_board import Board
    from .game_position import GamePosition
    from .move import Move



class Queen(Piece) :
    #: La dame réunit les lignes de la tour et les diagonales du fou.
    DIRECTIONS = ALL_DIRECTIONS

    def __init__(self, color) :
        super().__init__(color, "queen")


    def pseudo_moves(self, position: 'GamePosition', square: tuple) -> 'Iterator[Move]':
        """Produit les coups de la dame depuis ``square``, sans filtre de légalité."""
        return self._sliding_moves(position, square, self.DIRECTIONS)


    def _is_valid_move(self, square_from: tuple, square_to: tuple, board: 'Board'):
        BOARD = board.chessboard
        return MoveUtility._is_diag_valid(square_from, square_to, BOARD) or MoveUtility._is_line_valid(square_from, square_to, BOARD)


    def _move_piece(self, BOARD, square, add_or_remove):
        row, col = square
        # Change the board
        if add_or_remove == "add" :
            BOARD[row][col] = Queen(self.color)
        else :
            BOARD[row][col] = None
    

    def _can_move(self, board, square):
        ROW, COL = square
        for dr, dc in self.DIRECTIONS:
            if ROW+dr in range(8) and COL+dc in range(8) and self._is_valid_move(square, (ROW+dr, COL+dc), board):
                return True
        return False
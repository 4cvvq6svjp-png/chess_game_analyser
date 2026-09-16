from typing import TYPE_CHECKING

from .move import Move
from .pieces import Piece

if TYPE_CHECKING:
    from collections.abc import Iterator

    from .chess_board import Board
    from .game_position import GamePosition


class Knight (Piece) :
    #: Les huit sauts en L, seule géométrie que connaît le cavalier.
    OFFSETS = ((2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2))

    def __init__(self, color) :
        super().__init__(color, "knight")


    def pseudo_moves(self, position: 'GamePosition', square: tuple) -> 'Iterator[Move]':
        """Produit les coups du cavalier depuis ``square``.

        « Pseudo » parce que la légalité au sens du roi n'est pas vérifiée ici :
        un cavalier cloué produira quand même ses sauts. C'est
        ``GamePosition.legal_moves()`` qui écrira ce filtre -- une seule fois,
        pour toutes les pièces, au lieu de le réinventer dans chacune.
        """
        row, col = square
        for dr, dc in self.OFFSETS:
            landing = (row + dr, col + dc)
            if not (0 <= landing[0] < 8 and 0 <= landing[1] < 8):
                continue
            target = position.piece_at(landing)
            if target is not None and target.color == self.color:
                continue
            yield Move(square, landing)


    def _is_valid_move(self, square_from: tuple, square_to: tuple, board: 'Board'):
        BOARD = board.chessboard
        """Returns True is a proposed move that lands in the chessboard is valid"""
        row, col = square_from
        rowTO, colTO = square_to

        if not ((abs(row - rowTO) == 2 and abs(col - colTO) == 1) or (abs(row - rowTO) == 1 and abs(col - colTO) == 2)) :
            return False

        # landing square has a same color piece on it
        if (BOARD[rowTO][colTO] is not None) and (BOARD[row][col].color == BOARD[rowTO][colTO].color) :
            return False
        return True


    def _move_piece(self, BOARD, square, add_or_remove):
        row, col = square
        # Change the board
        if add_or_remove == "add" :
            BOARD[row][col] = Knight(self.color)
        else :
            BOARD[row][col] = None
    


    def _can_move(self, board, square):
        ROW, COL = square
        for dr, dc in self.OFFSETS:
            if ROW+dr in range(8) and COL+dc in range(8) and self._is_valid_move(square, (ROW+dr, COL+dc), board):
                return True
        return False
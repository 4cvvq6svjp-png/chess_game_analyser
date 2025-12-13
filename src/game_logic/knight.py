from pieces import Piece

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .chess_board import Board


class Knight (Piece) :
    def __init__(self, color) :
        super().__init__(color, "horse")

    
    def _is_valid_move(self, square_from: tuple, square_to: tuple, board: 'Board'):
        BOARD = board.chessboard
        """Returns True is a proposed move that lands in the chessboard is valid"""
        row, col = square_from
        rowTO, colTO = square_to

        if not ((abs(row - rowTO) == 2 and abs(col - colTO)) or (abs(row - rowTO) == 1 and abs(col - colTO) == 2)) :
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
        horse_square = [[2,1], [2,-1], [-2,1], [-2,-1], [1,2], [-1,2], [1,-2], [-1,-2]]
        for dr, dc in horse_square:
            if ROW+dr in range(8) and COL+dc in range(8) and self._is_valid_move(square, (ROW+dr, COL+dc), board):
                return True
        return False
from pieces import Piece
from move_utility import MoveUtility

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .chess_board import Board



class Queen(Piece) :
    def __init__(self, color) :
        super().__init__(color, "queen")



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
        directions = [[0,1], [1,0], [0,-1], [-1,0], [1,1], [1,-1], [-1,-1], [-1,1]]
        for dr, dc in directions:
            if ROW+dr in range(8) and COL+dc in range(8) and self._is_valid_move(square, (ROW+dr, COL+dc), board):
                return True
        return False
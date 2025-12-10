from pieces import Piece
from move_utility import MoveUtility

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .chess_board import Board


class King(Piece):

    def __init__(self, color) :
        super().__init__(color, "king")



    def _is_valid_move(self, square_from: tuple, square_to: tuple, board: 'Board'):
        BOARD = board.chessboard
        # check the length of the move
        if abs(square_to[0] - square_from[0]) > 1 or abs(square_to[1] - square_from[1]) > 1:
            return False

        rowTO, colTO = square_to

        return   MoveUtility.check_diags(BOARD, rowTO, colTO, self.color)["check"]\
             and MoveUtility.check_lines(BOARD, rowTO, colTO, self.color)["check"]\
             and MoveUtility.check_horses(BOARD, rowTO, colTO, self.color)["check"]



    def _move_piece(self, BOARD, square, add_or_remove):
        row, col = square
        # Change the board
        if add_or_remove == "add" :
            BOARD[row][col] = King(self.color)
        else :
            BOARD[row][col] = None


    def _can_move(self, board, square):
        ROW, COL = square
        directions = [[0,1], [1,0], [0,-1], [-1,0], [1,1], [1,-1], [-1,-1], [-1,1]]
        for dr, dc in directions:
            if ROW+dr in range(8) and COL+dc in range(8) and self._is_valid_move(square, (ROW+dr, COL+dc), board):
                return True
        return False
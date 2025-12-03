from pieces import Piece
from move_utility import MoveUtility


class Queen(Piece) :
    def __init__(self, color) :
        super().__init__(color, "queen")



    def _is_valid_move(self, square_from: tuple, square_to: tuple, BOARD: list[list['Piece']]):
        return MoveUtility._is_diag_valid(square_from, square_to, BOARD) or MoveUtility._is_line_valid(square_from, square_to, BOARD)


    def _move_piece(self, BOARD, square, add_or_remove):
        row, col = square
        # Change the board
        if add_or_remove == "add" :
            BOARD[row][col] = Queen(self.color)
        else :
            BOARD[row][col] = None
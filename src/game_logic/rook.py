from pieces import Piece
from move_utility import MoveUtility

class Rook(Piece) :
    def __init__(self, color) :
        super().__init__(color, "rook")


    def _is_valid_move(self, square_from: tuple, square_to: tuple, BOARD: list[list['Piece']]):
        return MoveUtility._is_line_valid(square_from, square_to, BOARD)
        


    def _move_piece(self, BOARD, square, add_or_remove):
        row, col = square
        # Change the board
        if add_or_remove == "add" :
            BOARD[row][col] = Rook(self.color)
        else :
            BOARD[row][col] = None

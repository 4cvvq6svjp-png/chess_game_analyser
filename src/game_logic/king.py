from pieces import Piece
from move_utility import MoveUtility


class King(Piece):
    DIRECTION = {"w": -1, "b": 1}

    def __init__(self, color) :
        super().__init__(color, "king")



    def _is_valid_move(self, square_from: tuple, square_to: tuple, BOARD: list[list['Piece']]):
        # check the length of the move
        if abs(square_to[0] - square_from[0]) > 1 or abs(square_to[1] - square_from[1]):
            return False

        rowTO, colTO = square_to
        m = self.DIRECTION[self.color]

        return MoveUtility.check_diags(BOARD, rowTO, colTO, m) and MoveUtility.check_lines(BOARD, rowTO, colTO) and MoveUtility.check_horses(BOARD, rowTO, colTO, self.color)



    def _move_piece(self, BOARD, square, add_or_remove):
        row, col = square
        # Change the board
        if add_or_remove == "add" :
            BOARD[row][col] = King(self.color)
        else :
            BOARD[row][col] = None
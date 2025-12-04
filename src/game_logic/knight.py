from pieces import Piece


class Knight (Piece) :
    def __init__(self, color) :
        super().__init__(color, "horse")



    
    def _is_valid_move(self, square_from: tuple, square_to: tuple, BOARD: list[list['Piece']]):
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
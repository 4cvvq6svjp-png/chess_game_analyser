from pieces import Piece

class Pawn (Piece) :
    #usefull constant
    DIRECTION = {"w": 1, "b": -1}
    MOVE = {"add" : 1, "remove" : -1}

    def __init__(self, color) :
        super.__init__(color)
        self.name = "pawn"

    def _is_valid_move(self, square_from: tuple, square_to: tuple):
        pass

    def _execute_move(self, square_from: tuple, square_to: tuple):
        pass

    def _move_piece(self, BOARD, take_board, square, add_or_remove):
        row, col = square
        dr = self.DIRECTION[self.color]
        m = self.MOVE[add_or_remove]

        # Change the take_board
        if row + dr in range(8) :
            if col - 1 in range(8):
                take_board[row][col-1][self.color] += 1*m
            if col + 1 in range(8) :
                take_board[row][col+1][self.color] += 1*m

        # Change the board
        if add_or_remove == "add" :
            BOARD[row][col] = Pawn(self.color)
        else :
            BOARD[row][col] = None

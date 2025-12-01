from pieces import Piece

class Pawn (Piece) :
    #usefull constant ??
    DIRECTION = {"w": 1, "b": -1}
    MOVE = {"add" : 1, "remove" : -1}

    def __init__(self, color) :
        super.__init__(color, "pawn")

    def _is_valid_move(self, square_from: tuple, square_to: tuple):
        pass

    def _execute_move(self, BOARD, square_from: tuple, square_to: tuple):
        self._move_piece(BOARD, square_from, "remove")
        self._move_piece(BOARD, square_to, "add")

    def _move_piece(self, BOARD, square, add_or_remove):
        row, col = square
        # Change the board
        if add_or_remove == "add" :
            BOARD[row][col] = Pawn(self.color)
        else :
            BOARD[row][col] = None

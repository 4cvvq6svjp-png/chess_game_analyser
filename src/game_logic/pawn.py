from pieces import Piece

class Pawn (Piece) :
    #usefull constant ??
    DIRECTION = {"w": 1, "b": -1}
    MOVE = {"add" : 1, "remove" : -1}

    def __init__(self, color) :
        super().__init__(color, "pawn")

    # the pawn is the only piece that moves differently if it is a take or not
    def _is_valid_move(self, square_from: tuple, square_to: tuple, BOARD: list[list['Piece']]):
        m = self.DIRECTION[self.color]
        # is it a take ?
        if abs(square_to[1] - square_to[1]) == 1 and square_to[0] - square_from[0] == m:
            landing_spot = BOARD[square_to[0], square_to[1]]
            if landing_spot is not None and landing_spot.color != self.color:
                return True
        
        # then it is a move forward
        if square_from[1] == square_to[1] and square_to[0] - square_from[0] == m :
            return True
        
        # two square move ? 
        if square_from[1] == square_to[1] and square_to[0] - square_from[0] == m*2 :
            return True
        return False
        


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

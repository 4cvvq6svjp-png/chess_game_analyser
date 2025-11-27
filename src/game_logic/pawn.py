from pieces import Piece

class Pawn (Piece) :
    #usefull constant
    DIRECTION = {"w": 1, "b": -1}
    MOVE = {"add" : 1, "remove" : -1}

    def __init__(self, couleur) :
        super.__init__(couleur)

    def _is_valid_move(square_from, square_to):
        pass

    def _execute_move(square_from, square_to):
        pass

    def _move_piece(self, take_board, r, c, add_or_remove):
        dr = self.DIRECTION[self.couleur]
        m = self.MOVE[add_or_remove]
        if r + dr in range(8) :
            if c - 1 in range(8):
                take_board[r][c-1][self.couleur] += 1*m
            if c + 1 in range(8) :
                take_board[r][c+1][self.couleur] += 1*m

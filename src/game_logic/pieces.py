from abc import ABC

class Piece(ABC):
    def __init__(self, color, name) :
        self.name = name
        self.color = color

    def _is_valid_move(self, square_from, square_to):
        pass

    def _execute_move(self):
        pass

    def _move_piece(self, board, r, c):
        pass


        
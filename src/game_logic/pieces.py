from abc import ABC

class Piece(ABC):
    def __init__(self, couleur) :
        self.couleur = couleur

    def _is_valid_move(self, square_from, square_to):
        pass

    def _is_taken(self):
        pass

    def _execute_move():
        pass

        
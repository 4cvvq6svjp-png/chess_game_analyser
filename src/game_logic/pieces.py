from abc import ABC, abstractmethod

class Piece(ABC):
    def __init__(self, color, name) :
        self.name = name
        self.color = color

    @abstractmethod
    def _is_valid_move(self, square_from, square_to, BOARD):
        pass
    
    @abstractmethod
    def _move_piece(self, board, square, add_or_remove):
        pass

    def _execute_move(self, BOARD, square_from: tuple, square_to: tuple):
        self._move_piece(BOARD, square_from, "remove")
        self._move_piece(BOARD, square_to, "add")




        
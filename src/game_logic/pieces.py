from abc import ABC, abstractmethod

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .chess_board import Board




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

    @abstractmethod
    def _can_move(self, board, square) :
        pass

    def _execute_move(self, board: 'Board', square_from: tuple, square_to: tuple):
        move = {"piece" : board.chessboard[square_from[0]][square_from[1]].name,
                "square_from" : square_from,
                "square_to" : square_to}
        self._move_piece(board.chessboard, square_from, "remove")
        self._move_piece(board.chessboard, square_to, "add")
        board.play_stack.append(move)




        
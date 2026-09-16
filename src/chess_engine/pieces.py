from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from .move import Move

if TYPE_CHECKING:
    from collections.abc import Iterator

    from .chess_board import Board
    from .game_position import GamePosition


#: Les quatre diagonales, les quatre lignes, et les huit réunies. Chaque pièce
#: déclare celles qui la concernent : la géométrie reste dans sa classe, seule
#: la façon de la parcourir est partagée.
DIAGONAL_DIRECTIONS = ((1, 1), (1, -1), (-1, 1), (-1, -1))
ORTHOGONAL_DIRECTIONS = ((0, 1), (0, -1), (1, 0), (-1, 0))
ALL_DIRECTIONS = ORTHOGONAL_DIRECTIONS + DIAGONAL_DIRECTIONS


class Piece(ABC):
    def __init__(self, color, name) :
        self.name = name
        self.color = color

    def _sliding_moves(self, position: 'GamePosition', square: tuple,
                       directions: tuple) -> 'Iterator[Move]':
        """Coups d'une pièce qui glisse : chaque direction jusqu'au premier obstacle.

        Une case occupée arrête la marche. Elle est tout de même produite si la
        pièce qui s'y trouve est adverse -- c'est une prise.
        """
        row, col = square
        for dr, dc in directions:
            r, c = row + dr, col + dc
            while 0 <= r < 8 and 0 <= c < 8:
                target = position.board[r][c]
                if target is not None:
                    if target.color != self.color:
                        yield Move(square, (r, c))
                    break
                yield Move(square, (r, c))
                r, c = r + dr, c + dc

    def _stepping_moves(self, position: 'GamePosition', square: tuple,
                        offsets: tuple) -> 'Iterator[Move]':
        """Coups d'une pièce qui ne fait qu'un bond : le roi et le cavalier.

        Une case hors échiquier ou tenue par une pièce amie est écartée ; tout
        le reste est produit, prise comprise.
        """
        row, col = square
        for dr, dc in offsets:
            landing = (row + dr, col + dc)
            if not (0 <= landing[0] < 8 and 0 <= landing[1] < 8):
                continue
            target = position.piece_at(landing)
            if target is not None and target.color == self.color:
                continue
            yield Move(square, landing)

    @abstractmethod
    def pseudo_moves(self, position: 'GamePosition', square: tuple) -> 'Iterator[Move]':
        """Produit les coups de la pièce depuis ``square``.

        « Pseudo » : la géométrie et les obstacles sont pris en compte, la
        légalité vis-à-vis du roi ne l'est pas. Toute pièce doit savoir
        répondre, car ``GamePosition.legal_moves()`` interrogera les six de la
        même façon, sans savoir laquelle elle tient.
        """

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




        
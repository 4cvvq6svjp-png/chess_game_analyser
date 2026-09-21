from typing import TYPE_CHECKING

from .pieces import ORTHOGONAL_DIRECTIONS, Piece

if TYPE_CHECKING:
    from collections.abc import Iterator

    from .game_position import GamePosition
    from .move import Move


class Rook(Piece):
    #: La tour ne connaît que les lignes et les colonnes.
    DIRECTIONS = ORTHOGONAL_DIRECTIONS

    def __init__(self, color):
        super().__init__(color, "rook")

    def pseudo_moves(self, position: 'GamePosition', square: tuple) -> 'Iterator[Move]':
        """Produit les coups de la tour depuis ``square``, sans filtre de légalité.

        Le roque n'apparaît pas ici : il déplace deux pièces et dépend des
        droits portés par la position, donc ``GamePosition.legal_moves()`` le
        produit elle-même.
        """
        return self._sliding_moves(position, square, self.DIRECTIONS)

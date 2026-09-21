from typing import TYPE_CHECKING

from .pieces import DIAGONAL_DIRECTIONS, Piece

if TYPE_CHECKING:
    from collections.abc import Iterator

    from .game_position import GamePosition
    from .move import Move


class Bishop(Piece):
    #: Le fou ne connaît que les diagonales.
    DIRECTIONS = DIAGONAL_DIRECTIONS

    def __init__(self, color):
        super().__init__(color, "bishop")

    def pseudo_moves(self, position: 'GamePosition', square: tuple) -> 'Iterator[Move]':
        """Produit les coups du fou depuis ``square``, sans filtre de légalité."""
        return self._sliding_moves(position, square, self.DIRECTIONS)

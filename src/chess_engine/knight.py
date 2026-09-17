from typing import TYPE_CHECKING

from .pieces import Piece

if TYPE_CHECKING:
    from collections.abc import Iterator

    from .game_position import GamePosition
    from .move import Move


class Knight(Piece):
    #: Les huit sauts en L, seule géométrie que connaît le cavalier.
    OFFSETS = ((2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2))

    def __init__(self, color):
        super().__init__(color, "knight")

    def pseudo_moves(self, position: 'GamePosition', square: tuple) -> 'Iterator[Move]':
        """Produit les sauts du cavalier depuis ``square``, sans filtre de légalité.

        Un cavalier cloué produit quand même ses sauts : c'est
        ``GamePosition.legal_moves()`` qui les écarte.
        """
        return self._stepping_moves(position, square, self.OFFSETS)

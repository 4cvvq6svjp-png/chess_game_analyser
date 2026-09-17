from typing import TYPE_CHECKING

from .pieces import ALL_DIRECTIONS, Piece

if TYPE_CHECKING:
    from collections.abc import Iterator

    from .game_position import GamePosition
    from .move import Move


class Queen(Piece):
    #: La dame réunit les lignes de la tour et les diagonales du fou.
    DIRECTIONS = ALL_DIRECTIONS

    def __init__(self, color):
        super().__init__(color, "queen")

    def pseudo_moves(self, position: 'GamePosition', square: tuple) -> 'Iterator[Move]':
        """Produit les coups de la dame depuis ``square``, sans filtre de légalité."""
        return self._sliding_moves(position, square, self.DIRECTIONS)

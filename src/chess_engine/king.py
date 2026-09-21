from typing import TYPE_CHECKING

from .pieces import ALL_DIRECTIONS, Piece

if TYPE_CHECKING:
    from collections.abc import Iterator

    from .game_position import GamePosition
    from .move import Move


class King(Piece):
    #: Le roi va dans les huit directions, mais d'un seul pas.
    DIRECTIONS = ALL_DIRECTIONS

    def __init__(self, color):
        super().__init__(color, "king")

    def pseudo_moves(self, position: 'GamePosition', square: tuple) -> 'Iterator[Move]':
        """Produit les huit pas du roi depuis ``square``, sans filtre de légalité.

        Les cases attaquées ne sont pas écartées ici : c'est
        ``GamePosition.legal_moves()`` qui applique le coup puis vérifie que le
        roi n'est pas en échec. L'évaluer après coup, sur une position où la
        case de départ est vide, est ce qui a fait disparaître le « king-shadow ».

        Le roque n'est pas produit ici non plus : il déplace deux pièces et
        dépend des droits portés par la position.
        """
        return self._stepping_moves(position, square, self.DIRECTIONS)

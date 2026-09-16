"""Le coup, tel que le générateur le produit.

Un ``Move`` est une donnée inerte : il décrit un déplacement, il ne sait pas
l'exécuter et ne dit pas s'il est légal. C'est ``GamePosition`` qui le jouera
(``apply``) et qui décidera de sa légalité (``legal_moves``).
"""

from __future__ import annotations

from dataclasses import dataclass

#: Suffixe utilisé en notation longue pour une promotion.
PROMOTION_LETTERS = {"queen": "q", "rook": "r", "bishop": "b", "knight": "n"}


def square_name(square: tuple[int, int]) -> str:
    """``(6, 4)`` -> ``"e2"``. Inverse de ``chess_game.coordinate``."""
    row, col = square
    return f"{chr(ord('a') + col)}{8 - row}"


@dataclass(frozen=True, slots=True)
class Move:
    """Un demi-coup : d'où, vers où, et en quoi le pion se transforme.

    Les cases sont en coordonnées moteur ``(row, col)``, où ``row 0`` est la
    rangée 8 et ``col 0`` la colonne a -- la convention de tout le moteur.

    ``promotion`` porte un nom de pièce (``"queen"``, ``"rook"``, ``"bishop"``,
    ``"knight"``), celui qu'attend ``Board.create_piece_by_name``.
    """

    square_from: tuple[int, int]
    square_to: tuple[int, int]
    promotion: str | None = None

    def __str__(self) -> str:
        """Notation longue : ``"g1f3"``, ``"e7e8q"`` pour une promotion."""
        text = square_name(self.square_from) + square_name(self.square_to)
        if self.promotion is not None:
            text += PROMOTION_LETTERS[self.promotion]
        return text

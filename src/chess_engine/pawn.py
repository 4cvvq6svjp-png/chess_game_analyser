from typing import TYPE_CHECKING

from .move import Move
from .pieces import Piece

if TYPE_CHECKING:
    from collections.abc import Iterator

    from .game_position import GamePosition


class Pawn(Piece):
    DIRECTION = {"w": -1, "b": 1}

    #: Ce qu'un pion peut devenir en atteignant la dernière rangée.
    PROMOTION_CHOICES = ("queen", "rook", "bishop", "knight")

    def __init__(self, color):
        super().__init__(color, "pawn")

    def starting_rank(color):
        return 6 if color == "w" else 1

    def back_rank(color):
        return 0 if color == "w" else 7

    def pseudo_moves(self, position: 'GamePosition', square: tuple) -> 'Iterator[Move]':
        """Produit les coups du pion depuis ``square``, sans filtre de légalité.

        Le pion est la seule pièce dont les coups ne se lisent pas entièrement
        sur la grille : la prise en passant dépend du coup précédent, que la
        position porte dans ``en_passant_square``. C'est aussi la seule dont un
        déplacement peut produire *quatre* coups -- une promotion par pièce
        possible -- là où les autres en produisent un.
        """
        row, col = square
        m = self.DIRECTION[self.color]
        forward = row + m
        if not 0 <= forward < 8:
            return

        # le pas en avant, et le bond de deux depuis la rangée de départ
        if position.board[forward][col] is None:
            yield from self._push_or_promote(square, (forward, col))
            if row == Pawn.starting_rank(self.color):
                double = row + 2 * m
                if position.board[double][col] is None:
                    yield Move(square, (double, col))

        # les deux prises en diagonale
        for dc in (-1, 1):
            landing = (forward, col + dc)
            if not 0 <= landing[1] < 8:
                continue
            target = position.piece_at(landing)
            if target is not None:
                if target.color != self.color:
                    yield from self._push_or_promote(square, landing)
            elif landing == position.en_passant_square and self._victim_is_there(
                position, landing
            ):
                yield Move(square, landing)

    def _push_or_promote(self, square: tuple, landing: tuple) -> 'Iterator[Move]':
        """Un coup, ou les quatre promotions si l'arrivée est la dernière rangée."""
        if landing[0] == Pawn.back_rank(self.color):
            for piece_name in self.PROMOTION_CHOICES:
                yield Move(square, landing, piece_name)
        else:
            yield Move(square, landing)

    def _victim_is_there(self, position: 'GamePosition', landing: tuple) -> bool:
        """La case d'en passant ne vaut que si le pion à prendre est bien là.

        Il se tient à côté du pion qui capture, sur la rangée que celui-ci
        quitte -- jamais sur la case d'arrivée, d'où cette vérification à part.
        """
        victim = position.piece_at((landing[0] - self.DIRECTION[self.color], landing[1]))
        return victim is not None and victim.name == "pawn" and victim.color != self.color

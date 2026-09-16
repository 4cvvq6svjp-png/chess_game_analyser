"""L'état complet d'une partie à un instant donné.

Une disposition de pièces ne suffit pas à dire quels coups sont jouables : la
prise en passant dépend du coup précédent, le roque de ce que les pièces ont
fait plus tôt, la nulle des compteurs. ``GamePosition`` réunit ces six
informations -- exactement les six champs d'une FEN, ce qui n'est pas un
hasard : la FEN est la notation d'une position.

L'objet est immuable. ``apply(move)`` (à venir) renverra une *nouvelle*
position au lieu de modifier celle-ci, ce qui rend le rembobinage et
l'exploration d'arbre triviaux : rien n'est jamais annulé.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .chess_board import Board
    from .pieces import Piece

#: Tous les droits de roque, comme le ``KQkq`` d'une FEN.
ALL_CASTLING_RIGHTS = frozenset("KQkq")


@dataclass(frozen=True, slots=True)
class GamePosition:
    """Une position : la partie telle qu'elle se présente à celui qui doit jouer.

    ``board[row][col]`` suit la convention du moteur : ``row 0`` est la rangée
    8, ``col 0`` la colonne a. Les rangées sont des tuples, pour que la
    position reste réellement immuable.
    """

    board: tuple[tuple[Piece | None, ...], ...]
    side_to_move: str = "w"
    castling_rights: frozenset[str] = ALL_CASTLING_RIGHTS
    en_passant_square: tuple[int, int] | None = None
    halfmove_clock: int = 0
    fullmove_number: int = 1

    def piece_at(self, square: tuple[int, int]) -> Piece | None:
        """La pièce sur ``square``, ou ``None``. Ne vérifie pas les bornes."""
        row, col = square
        return self.board[row][col]

    @classmethod
    def from_board(
        cls,
        board: Board,
        side_to_move: str = "w",
        castling_rights: frozenset[str] = ALL_CASTLING_RIGHTS,
    ) -> GamePosition:
        """Construit une position depuis le ``Board`` historique.

        Passerelle de migration : elle laisse le code existant (et ses tests)
        alimenter le nouveau noyau tant que ``from_fen`` n'existe pas.

        La case d'en passant est déduite du dernier coup empilé, seul endroit
        où l'information vit aujourd'hui. Les droits de roque, eux, ne sont
        *pas* déductibles d'un ``Board`` -- il ne garde pas trace de ce qui a
        bougé -- d'où le paramètre explicite.
        """
        return cls(
            board=tuple(tuple(row) for row in board.chessboard),
            side_to_move=side_to_move,
            castling_rights=castling_rights,
            en_passant_square=_en_passant_square(board),
        )


def _en_passant_square(board: Board) -> tuple[int, int] | None:
    """La case survolée par le dernier coup, s'il s'agit d'un bond de pion.

    C'est la case d'arrivée d'une éventuelle prise en passant, celle que la
    FEN note juste après le trait.
    """
    if not board.play_stack:
        return None
    last = board.play_stack[-1]
    row_from, col = last["square_from"]
    row_to, _ = last["square_to"]
    if last["piece"] != "pawn" or abs(row_from - row_to) != 2:
        return None
    return ((row_from + row_to) // 2, col)

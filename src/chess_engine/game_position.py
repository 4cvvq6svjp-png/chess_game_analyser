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

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from .bishop import Bishop
from .knight import Knight
from .move_utility import MoveUtility
from .pawn import Pawn
from .queen import Queen
from .rook import Rook

if TYPE_CHECKING:
    from .chess_board import Board
    from .move import Move
    from .pieces import Piece

#: Tous les droits de roque, comme le ``KQkq`` d'une FEN.
ALL_CASTLING_RIGHTS = frozenset("KQkq")

#: Ce qu'un pion peut devenir. Les noms sont ceux que porte ``Move.promotion``.
PROMOTION_PIECES = {"queen": Queen, "rook": Rook, "bishop": Bishop, "knight": Knight}

#: Le droit de roque que chaque coin fait perdre, que la tour le quitte ou
#: qu'elle s'y fasse prendre.
ROOK_HOME_SQUARES = {
    (7, 0): frozenset("Q"),
    (7, 7): frozenset("K"),
    (0, 0): frozenset("q"),
    (0, 7): frozenset("k"),
}


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

    def find_king(self, color: str) -> tuple[int, int] | None:
        """La case du roi de ``color``, ou ``None`` s'il n'y en a pas.

        Un échiquier sans roi n'existe pas en partie, mais les tests en
        construisent -- une pièce seule sur un plateau vide.
        """
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece is not None and piece.name == "king" and piece.color == color:
                    return (row, col)
        return None

    def is_in_check(self, color: str) -> bool:
        """Le roi de ``color`` est-il attaqué dans cette position ?"""
        square = self.find_king(color)
        if square is None:
            return False
        row, col = square
        # Les check_* de MoveUtility répondent à l'envers : "check": False
        # signifie que la case *est* attaquée.
        return not (
            MoveUtility.check_diags(self.board, row, col, color)["check"]
            and MoveUtility.check_lines(self.board, row, col, color)["check"]
            and MoveUtility.check_knights(self.board, row, col, color)["check"]
        )

    def legal_moves(self) -> list[Move]:
        """Tous les coups jouables par le camp au trait.

        Les pièces produisent leurs coups pseudo-légaux, et un seul filtre les
        trie : le coup est illégal s'il laisse son propre roi en échec. Écrit
        une fois ici, ce filtre couvre d'un coup les clouages, les échecs
        découverts et les fuites du roi -- y compris le cas où le roi glisse le
        long de la ligne qui l'attaque, puisque ``apply`` a vidé sa case de
        départ avant l'évaluation.

        Le roque n'est pas encore produit : il viendra ici même, en lisant
        ``castling_rights``.
        """
        moves = []
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece is None or piece.color != self.side_to_move:
                    continue
                for move in piece.pseudo_moves(self, (row, col)):
                    if not self.apply(move).is_in_check(self.side_to_move):
                        moves.append(move)
        return moves

    def apply(self, move: Move) -> GamePosition:
        """Joue ``move`` et renvoie la position qui en résulte.

        Ne modifie rien : la position courante reste intacte, ce qui rend le
        rembobinage et l'exploration d'arbre triviaux. Seule la grille est
        recopiée ; les pièces, qui n'ont pas d'état, sont partagées.
        """
        piece = self.piece_at(move.square_from)
        row_from, col_from = move.square_from
        row_to, col_to = move.square_to

        grid = [list(row) for row in self.board]
        captured = self.piece_at(move.square_to)
        grid[row_from][col_from] = None

        # Prise en passant : le pion pris n'est pas sur la case d'arrivée mais
        # à côté du pion qui capture.
        if (
            piece.name == "pawn"
            and captured is None
            and move.square_to == self.en_passant_square
        ):
            victim_row = row_to - Pawn.DIRECTION[piece.color]
            captured = grid[victim_row][col_to]
            grid[victim_row][col_to] = None

        if move.promotion is not None:
            grid[row_to][col_to] = PROMOTION_PIECES[move.promotion](piece.color)
        else:
            grid[row_to][col_to] = piece

        return replace(
            self,
            board=tuple(tuple(row) for row in grid),
            side_to_move="b" if self.side_to_move == "w" else "w",
            castling_rights=self._castling_rights_after(move, piece),
            en_passant_square=self._en_passant_square_after(move, piece),
            halfmove_clock=(
                0 if piece.name == "pawn" or captured is not None
                else self.halfmove_clock + 1
            ),
            fullmove_number=self.fullmove_number + (1 if self.side_to_move == "b" else 0),
        )

    def _castling_rights_after(self, move: Move, piece: Piece) -> frozenset[str]:
        """Les droits restants : le roi qui bouge les perd tous, un coin les perd un."""
        if not self.castling_rights:
            return self.castling_rights
        lost = frozenset("KQ" if piece.color == "w" else "kq") if piece.name == "king" \
            else frozenset()
        for square in (move.square_from, move.square_to):
            lost |= ROOK_HOME_SQUARES.get(square, frozenset())
        return self.castling_rights - lost

    def _en_passant_square_after(self, move: Move, piece: Piece) -> tuple[int, int] | None:
        """Un bond de pion ouvre la case qu'il survole ; tout autre coup la referme."""
        row_from = move.square_from[0]
        row_to = move.square_to[0]
        if piece.name == "pawn" and abs(row_to - row_from) == 2:
            return ((row_from + row_to) // 2, move.square_from[1])
        return None

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

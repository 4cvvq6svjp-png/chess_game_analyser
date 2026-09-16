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
from typing import TYPE_CHECKING, NamedTuple

from .bishop import Bishop
from .king import King
from .knight import Knight
from .move import Move, square_from_name, square_name
from .move_utility import MoveUtility
from .pawn import Pawn
from .queen import Queen
from .rook import Rook

if TYPE_CHECKING:
    from collections.abc import Iterator

    from .chess_board import Board
    from .pieces import Piece

#: Tous les droits de roque, comme le ``KQkq`` d'une FEN.
ALL_CASTLING_RIGHTS = frozenset("KQkq")

#: La lettre de chaque pièce, telle que l'écrivent la FEN et la notation
#: algébrique : majuscule pour les blancs, minuscule pour les noirs. Le
#: cavalier prend N, le K étant celui du roi. Source unique -- l'affichage
#: terminal et l'export FEN lisent la même table.
PIECE_CLASSES_BY_LETTER = {
    "k": King,
    "q": Queen,
    "r": Rook,
    "b": Bishop,
    "n": Knight,
    "p": Pawn,
}
LETTERS_BY_NAME = {
    piece_class("w").name: letter.upper()
    for letter, piece_class in PIECE_CLASSES_BY_LETTER.items()
}

#: Ce qu'un pion peut devenir. Les noms sont ceux que porte ``Move.promotion``.
PROMOTION_PIECES = {"queen": Queen, "rook": Rook, "bishop": Bishop, "knight": Knight}

#: Le droit de roque que chaque coin fait perdre, que la tour le quitte ou
#: qu'elle s'y fasse prendre.
ROOK_HOME_SQUARES = {
    square_from_name("a1"): frozenset("Q"),
    square_from_name("h1"): frozenset("K"),
    square_from_name("a8"): frozenset("q"),
    square_from_name("h8"): frozenset("k"),
}


class Castling(NamedTuple):
    """Le parcours d'un roque, et ses deux conditions de case.

    ``must_be_empty`` et ``must_be_safe`` ne se recouvrent pas : au grand
    roque, la case b1 doit être libre alors que le roi ne la traverse pas,
    et e1 doit être sûre -- on ne roque pas en étant en échec -- alors qu'elle
    n'a pas à être vide, le roi s'y trouvant.
    """

    king_from: tuple[int, int]
    king_to: tuple[int, int]
    rook_from: tuple[int, int]
    rook_to: tuple[int, int]
    must_be_empty: tuple[tuple[int, int], ...]
    must_be_safe: tuple[tuple[int, int], ...]


#: Les quatre roques, indexés par la lettre que leur donne la FEN.
CASTLINGS = {
    "K": Castling(
        square_from_name("e1"), square_from_name("g1"),
        square_from_name("h1"), square_from_name("f1"),
        must_be_empty=(square_from_name("f1"), square_from_name("g1")),
        must_be_safe=(square_from_name("e1"), square_from_name("f1"),
                      square_from_name("g1")),
    ),
    "Q": Castling(
        square_from_name("e1"), square_from_name("c1"),
        square_from_name("a1"), square_from_name("d1"),
        must_be_empty=(square_from_name("b1"), square_from_name("c1"),
                       square_from_name("d1")),
        must_be_safe=(square_from_name("e1"), square_from_name("d1"),
                      square_from_name("c1")),
    ),
    "k": Castling(
        square_from_name("e8"), square_from_name("g8"),
        square_from_name("h8"), square_from_name("f8"),
        must_be_empty=(square_from_name("f8"), square_from_name("g8")),
        must_be_safe=(square_from_name("e8"), square_from_name("f8"),
                      square_from_name("g8")),
    ),
    "q": Castling(
        square_from_name("e8"), square_from_name("c8"),
        square_from_name("a8"), square_from_name("d8"),
        must_be_empty=(square_from_name("b8"), square_from_name("c8"),
                       square_from_name("d8")),
        must_be_safe=(square_from_name("e8"), square_from_name("d8"),
                      square_from_name("c8")),
    ),
}

#: Les droits que chaque camp peut encore exercer.
CASTLING_RIGHTS_BY_COLOR = {"w": ("K", "Q"), "b": ("k", "q")}


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

    def is_attacked(self, square: tuple[int, int], color: str) -> bool:
        """La case est-elle attaquée par l'adversaire de ``color`` ?

        Utile au-delà de l'échec : le roque exige que trois cases soient sûres,
        dont deux qui ne portent pas le roi.
        """
        row, col = square
        # Les check_* de MoveUtility répondent à l'envers : "check": False
        # signifie que la case *est* attaquée.
        return not (
            MoveUtility.check_diags(self.board, row, col, color)["check"]
            and MoveUtility.check_lines(self.board, row, col, color)["check"]
            and MoveUtility.check_knights(self.board, row, col, color)["check"]
        )

    def is_in_check(self, color: str) -> bool:
        """Le roi de ``color`` est-il attaqué dans cette position ?"""
        square = self.find_king(color)
        return False if square is None else self.is_attacked(square, color)

    def legal_moves(self) -> list[Move]:
        """Tous les coups jouables par le camp au trait.

        Les pièces produisent leurs coups pseudo-légaux, et un seul filtre les
        trie : le coup est illégal s'il laisse son propre roi en échec. Écrit
        une fois ici, ce filtre couvre d'un coup les clouages, les échecs
        découverts et les fuites du roi -- y compris le cas où le roi glisse le
        long de la ligne qui l'attaque, puisque ``apply`` a vidé sa case de
        départ avant l'évaluation.

        Le roque est produit ici et non par une pièce : il en déplace deux, et
        ses conditions tiennent à la position -- les droits restants et la
        sûreté des cases traversées.
        """
        moves = []
        candidates = (
            (piece, (row, col))
            for row in range(8)
            for col in range(8)
            if (piece := self.board[row][col]) is not None
            and piece.color == self.side_to_move
        )
        for piece, square in candidates:
            for move in piece.pseudo_moves(self, square):
                if not self.apply(move).is_in_check(self.side_to_move):
                    moves.append(move)

        for move in self._castling_moves():
            if not self.apply(move).is_in_check(self.side_to_move):
                moves.append(move)
        return moves

    def _castling_moves(self) -> Iterator[Move]:
        """Les roques encore possibles pour le camp au trait.

        Le coup est représenté par le seul déplacement du roi, de deux cases --
        la notation qu'emploient l'UCI et la plupart des moteurs. ``apply``
        reconnaît ce saut et déplace la tour avec lui.
        """
        for right in CASTLING_RIGHTS_BY_COLOR[self.side_to_move]:
            if right not in self.castling_rights:
                continue
            plan = CASTLINGS[right]

            # Une FEN peut annoncer un droit sans les pièces qui vont avec.
            king = self.piece_at(plan.king_from)
            rook = self.piece_at(plan.rook_from)
            if king is None or king.name != "king" or king.color != self.side_to_move:
                continue
            if rook is None or rook.name != "rook" or rook.color != self.side_to_move:
                continue

            if any(self.piece_at(square) is not None for square in plan.must_be_empty):
                continue
            if any(
                self.is_attacked(square, self.side_to_move)
                for square in plan.must_be_safe
            ):
                continue
            yield Move(plan.king_from, plan.king_to)

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

        # Roque : le saut de deux cases du roi entraîne la tour avec lui.
        if piece.name == "king" and abs(col_to - col_from) == 2:
            rook_from_col, rook_to_col = (7, 5) if col_to > col_from else (0, 3)
            grid[row_from][rook_to_col] = grid[row_from][rook_from_col]
            grid[row_from][rook_from_col] = None

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

    def to_fen(self) -> str:
        """La position écrite en FEN.

        Les six champs de la notation sont les six champs de cette classe, dans
        l'ordre : placement, trait, droits de roque, case d'en passant, demi-coups
        depuis la dernière prise ou poussée, numéro du coup.
        """
        ranks = []
        for row in self.board:
            text = ""
            empty = 0
            for piece in row:
                if piece is None:
                    empty += 1
                    continue
                if empty:
                    text += str(empty)
                    empty = 0
                letter = LETTERS_BY_NAME[piece.name]
                text += letter if piece.color == "w" else letter.lower()
            if empty:
                text += str(empty)
            ranks.append(text)

        castling = "".join(right for right in "KQkq" if right in self.castling_rights)
        en_passant = (
            square_name(self.en_passant_square) if self.en_passant_square else "-"
        )
        return " ".join([
            "/".join(ranks),
            self.side_to_move,
            castling or "-",
            en_passant,
            str(self.halfmove_clock),
            str(self.fullmove_number),
        ])

    @classmethod
    def from_fen(cls, fen: str) -> GamePosition:
        """Construit une position depuis une FEN.

        Les deux compteurs finaux sont facultatifs : beaucoup de positions de
        test publiées s'arrêtent après la case d'en passant. Ils valent alors
        0 et 1, ce qui ne change rien au calcul des coups.
        """
        fields = fen.split()
        if len(fields) < 4:
            raise ValueError(f"FEN incomplète, 4 champs au minimum : {fen!r}")

        placement, side_to_move, castling, en_passant = fields[:4]
        if side_to_move not in ("w", "b"):
            raise ValueError(f"trait invalide : {side_to_move!r}")

        rows = placement.split("/")
        if len(rows) != 8:
            raise ValueError(f"placement : 8 rangées attendues, {len(rows)} reçues")

        board = []
        for index, text in enumerate(rows):
            row = []
            for character in text:
                if character.isdigit():
                    row.extend([None] * int(character))
                    continue
                piece_class = PIECE_CLASSES_BY_LETTER.get(character.lower())
                if piece_class is None:
                    raise ValueError(f"pièce inconnue dans la FEN : {character!r}")
                row.append(piece_class("w" if character.isupper() else "b"))
            if len(row) != 8:
                raise ValueError(
                    f"rangée {8 - index} : 8 cases attendues, {len(row)} décrites"
                )
            board.append(tuple(row))

        unknown = set(castling) - set("KQkq-")
        if unknown:
            raise ValueError(f"droits de roque invalides : {sorted(unknown)}")

        return cls(
            board=tuple(board),
            side_to_move=side_to_move,
            castling_rights=frozenset(castling) - {"-"},
            en_passant_square=(
                None if en_passant == "-" else square_from_name(en_passant)
            ),
            halfmove_clock=int(fields[4]) if len(fields) > 4 else 0,
            fullmove_number=int(fields[5]) if len(fields) > 5 else 1,
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

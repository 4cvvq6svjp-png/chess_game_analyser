"""Outillage commun aux tests.

Le moteur est installé comme paquet ``chess_engine`` (``pip install -e .``),
donc les tests l'importent par son nom.

Convention de coordonnées (celle du moteur) : ``board[row][col]``, ``row 0``
est la rangée 8 et ``col 0`` la colonne a. Les tests écrivent les cases en
notation d'échecs -- ``square("e4")`` -- parce qu'une position doit se relire
d'un coup d'œil.
"""

from chess_engine import (
    Bishop,
    Game,
    GamePosition,
    King,
    Knight,
    Move,
    Pawn,
    Piece,
    Queen,
    Rook,
    Status,
    square_from_name,
    square_name,
)

__all__ = [
    "Bishop",
    "Game",
    "GamePosition",
    "King",
    "Knight",
    "Move",
    "Pawn",
    "Piece",
    "Queen",
    "Rook",
    "Status",
    "position_with",
    "square",
    "square_from_name",
    "square_name",
]

#: ``square("e2")`` -> ``(6, 4)``. C'est la fonction du moteur, pas une copie.
square = square_from_name


def position_with(
    pieces,
    side_to_move="w",
    castling="-",
    en_passant="-",
    halfmove=0,
    fullmove=1,
):
    """Une position bâtie pièce par pièce, sans écrire de FEN complète.

        position_with({"e4": Knight("w"), "d5": Pawn("b")})

    Pratique quand seules deux ou trois pièces comptent ; pour une position
    réaliste, ``GamePosition.from_fen`` reste plus lisible.
    """
    grid = [[None] * 8 for _ in range(8)]
    for name, piece in pieces.items():
        row, col = square(name)
        grid[row][col] = piece
    return GamePosition(
        board=tuple(tuple(row) for row in grid),
        side_to_move=side_to_move,
        castling_rights=frozenset(castling) - {"-"},
        en_passant_square=None if en_passant == "-" else square(en_passant),
        halfmove_clock=halfmove,
        fullmove_number=fullmove,
    )

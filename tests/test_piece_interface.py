"""Le contrat commun aux six pièces.

``GamePosition.legal_moves()`` parcourt l'échiquier et demande ses coups à
chaque pièce sans savoir laquelle elle tient. Ces tests vérifient que cet
appel polymorphe fonctionne pour les six, et que le contrat est tenu par la
classe de base plutôt que par la discipline.
"""

import unittest

from helpers import (
    Bishop,
    King,
    Knight,
    Move,
    Pawn,
    Piece,
    Queen,
    Rook,
    position_with,
    square,
    square_name,
)

CENTRE = square("e4")
ALL_PIECES = (Bishop, King, Knight, Pawn, Queen, Rook)


class TestEveryPieceGenerates(unittest.TestCase):
    def moves_from(self, position, origin):
        return list(position.piece_at(origin).pseudo_moves(position, origin))

    def test_each_kind_yields_moves_anchored_on_its_square(self):
        for kind in ALL_PIECES:
            with self.subTest(piece=kind.__name__):
                position = position_with({"e4": kind("w")})
                moves = self.moves_from(position, CENTRE)
                self.assertTrue(moves, f"{kind.__name__} ne produit aucun coup")
                self.assertTrue(all(isinstance(m, Move) for m in moves))
                self.assertTrue(all(m.square_from == CENTRE for m in moves))

    def test_no_move_ever_leaves_the_board(self):
        for kind in ALL_PIECES:
            for name in ["a8", "h8", "a2", "h2", "d4"]:
                with self.subTest(piece=kind.__name__, origin=name):
                    position = position_with({name: kind("b")}, side_to_move="b")
                    for move in self.moves_from(position, square(name)):
                        row, col = move.square_to
                        self.assertTrue(0 <= row < 8 and 0 <= col < 8)

    def test_no_piece_ever_stands_still(self):
        for kind in ALL_PIECES:
            with self.subTest(piece=kind.__name__):
                position = position_with({"e4": kind("w")})
                destinations = {m.square_to for m in self.moves_from(position, CENTRE)}
                self.assertNotIn(CENTRE, destinations)

    def test_a_piece_never_lands_on_a_friend(self):
        """Un échiquier saturé d'amis : plus aucun coup, pour aucune pièce."""
        for kind in ALL_PIECES:
            with self.subTest(piece=kind.__name__):
                pieces = {
                    square_name((row, col)): Pawn("w")
                    for row in range(8)
                    for col in range(8)
                }
                pieces["e4"] = kind("w")
                position = position_with(pieces)
                self.assertEqual(self.moves_from(position, CENTRE), [])

    def test_the_call_is_polymorphic(self):
        """Le site d'appel ne connaît que Piece."""
        position = position_with(
            {"b1": Knight("w"), "a1": Rook("w"), "d2": Pawn("w")}
        )
        generated = []
        for name in ["b1", "a1", "d2"]:
            piece = position.piece_at(square(name))
            self.assertIsInstance(piece, Piece)
            generated.extend(piece.pseudo_moves(position, square(name)))

        self.assertTrue(generated)
        self.assertTrue(all(isinstance(m, Move) for m in generated))


class TestTheContractIsEnforced(unittest.TestCase):
    def test_a_piece_without_a_generator_cannot_exist(self):
        class Ghost(Piece):
            pass

        with self.assertRaises(TypeError):
            Ghost("w", "ghost")


if __name__ == "__main__":
    unittest.main()

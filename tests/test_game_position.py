"""La position comme valeur : lecture, immutabilité, champs.

La construction depuis une FEN est couverte par test_fen ; ici on vérifie ce
que l'objet garantit une fois bâti.
"""

import unittest

from helpers import GamePosition, King, Knight, Pawn, position_with, square


class TestReading(unittest.TestCase):
    def test_piece_at_reads_the_grid(self):
        knight = Knight("b")
        position = position_with({"g8": knight})
        self.assertIs(position.piece_at(square("g8")), knight)
        self.assertIsNone(position.piece_at(square("d4")))

    def test_find_king_locates_each_side(self):
        position = position_with({"e1": King("w"), "e8": King("b")})
        self.assertEqual(position.find_king("w"), square("e1"))
        self.assertEqual(position.find_king("b"), square("e8"))

    def test_find_king_returns_none_when_there_is_none(self):
        """Les tests construisent des échiquiers sans roi ; le moteur l'accepte."""
        self.assertIsNone(position_with({"e4": Knight("w")}).find_king("w"))

    def test_a_kingless_side_is_never_in_check(self):
        self.assertFalse(position_with({"e4": Knight("w")}).is_in_check("w"))


class TestTheFields(unittest.TestCase):
    def test_defaults_describe_a_fresh_position(self):
        position = position_with({})
        self.assertEqual(position.side_to_move, "w")
        self.assertEqual(position.halfmove_clock, 0)
        self.assertEqual(position.fullmove_number, 1)
        self.assertIsNone(position.en_passant_square)

    def test_they_are_carried_as_given(self):
        position = position_with(
            {"e1": King("w")},
            side_to_move="b",
            castling="Kq",
            en_passant="e6",
            halfmove=17,
            fullmove=42,
        )
        self.assertEqual(position.side_to_move, "b")
        self.assertEqual(position.castling_rights, frozenset("Kq"))
        self.assertEqual(position.en_passant_square, square("e6"))
        self.assertEqual(position.halfmove_clock, 17)
        self.assertEqual(position.fullmove_number, 42)


class TestImmutability(unittest.TestCase):
    def test_the_grid_is_made_of_tuples(self):
        position = position_with({"e4": Knight("w")})
        self.assertIsInstance(position.board, tuple)
        self.assertIsInstance(position.board[0], tuple)

    def test_the_fields_cannot_be_reassigned(self):
        position = position_with({})
        with self.assertRaises(Exception):
            position.side_to_move = "b"

    def test_applying_a_move_leaves_the_original_alone(self):
        before = position_with({"e2": Pawn("w"), "e1": King("w"), "e8": King("b")})
        fen_before = before.to_fen()
        after = before.apply(next(m for m in before.legal_moves() if str(m) == "e2e4"))

        self.assertEqual(before.to_fen(), fen_before)
        self.assertNotEqual(after.to_fen(), fen_before)
        self.assertIsNotNone(before.piece_at(square("e2")))
        self.assertIsNone(after.piece_at(square("e2")))

    def test_pieces_are_shared_rather_than_copied(self):
        """Une pièce n'a pas d'état : la recopier ne servirait à rien."""
        knight = Knight("w")
        before = position_with({"b1": knight, "e1": King("w"), "e8": King("b")})
        after = before.apply(next(m for m in before.legal_moves() if str(m) == "b1c3"))
        self.assertIs(after.piece_at(square("c3")), knight)


class TestEquality(unittest.TestCase):
    def test_the_fen_is_the_identity_not_the_object(self):
        """Deux positions identiques portent des instances de pièces distinctes."""
        one = position_with({"e4": Knight("w")})
        other = position_with({"e4": Knight("w")})
        self.assertNotEqual(one, other)
        self.assertEqual(one.to_fen(), other.to_fen())
        self.assertEqual(one.repetition_key(), other.repetition_key())

    def test_a_position_can_be_rebuilt_from_its_fen(self):
        position = position_with({"e4": Knight("w"), "e1": King("w")}, castling="K")
        self.assertEqual(GamePosition.from_fen(position.to_fen()).to_fen(), position.to_fen())


if __name__ == "__main__":
    unittest.main()

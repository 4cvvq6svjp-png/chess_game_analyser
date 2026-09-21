"""Le roque : la seule règle où un coup déplace deux pièces.

Il est produit par la position et non par une pièce, parce que ses conditions
ne sont pas géométriques : des droits hérités de toute la partie, des cases
vides, et des cases sûres -- trois ensembles qui ne se confondent pas.
"""

import unittest

from helpers import GamePosition, square

#: Roques disponibles des deux côtés, avec les rangées de pions intactes.
OPEN = "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1"


def moves_of(fen):
    return {str(move) for move in GamePosition.from_fen(fen).legal_moves()}


def play(fen, text):
    position = GamePosition.from_fen(fen)
    move = next((m for m in position.legal_moves() if str(m) == text), None)
    assert move is not None, f"{text} n'est pas légal dans {fen}"
    return position.apply(move)


class TestTheCastlesAreGenerated(unittest.TestCase):
    def test_white_has_both(self):
        self.assertTrue({"e1g1", "e1c1"} <= moves_of(OPEN))

    def test_black_has_both(self):
        black_to_move = OPEN.replace(" w ", " b ")
        self.assertTrue({"e8g8", "e8c8"} <= moves_of(black_to_move))

    def test_none_appear_without_the_rights(self):
        stripped = OPEN.replace(" KQkq ", " - ")
        self.assertFalse({"e1g1", "e1c1"} & moves_of(stripped))

    def test_declared_rights_without_the_rooks_are_ignored(self):
        """Une FEN peut mentir : les droits ne créent pas les pièces."""
        self.assertFalse({"e1g1", "e1c1"} & moves_of("4k3/8/8/8/8/8/8/4K3 w KQkq - 0 1"))


class TestTheRookFollows(unittest.TestCase):
    def test_kingside_puts_the_rook_on_f1(self):
        after = play(OPEN, "e1g1")
        self.assertEqual(after.piece_at(square("g1")).name, "king")
        self.assertEqual(after.piece_at(square("f1")).name, "rook")
        self.assertIsNone(after.piece_at(square("e1")))
        self.assertIsNone(after.piece_at(square("h1")))

    def test_queenside_puts_the_rook_on_d1(self):
        after = play(OPEN, "e1c1")
        self.assertEqual(after.piece_at(square("c1")).name, "king")
        self.assertEqual(after.piece_at(square("d1")).name, "rook")
        self.assertIsNone(after.piece_at(square("a1")))

    def test_black_castles_on_its_own_rank(self):
        after = play(OPEN.replace(" w ", " b "), "e8g8")
        self.assertEqual(after.piece_at(square("g8")).name, "king")
        self.assertEqual(after.piece_at(square("f8")).name, "rook")

    def test_the_move_is_written_as_the_kings_two_squares(self):
        self.assertIn("e1g1", moves_of(OPEN))


class TestRightsAreSpent(unittest.TestCase):
    def test_the_king_loses_both(self):
        after = play(OPEN, "e1f1")
        self.assertEqual(after.castling_rights, frozenset("kq"))

    def test_a_rook_loses_its_own_side(self):
        self.assertEqual(play(OPEN, "h1g1").castling_rights, frozenset("Qkq"))
        self.assertEqual(play(OPEN, "a1b1").castling_rights, frozenset("Kkq"))

    def test_castling_itself_spends_them(self):
        self.assertEqual(play(OPEN, "e1g1").castling_rights, frozenset("kq"))

    def test_a_rook_taken_on_its_corner_loses_the_right(self):
        """La tour noire prend en h1 : les blancs perdent K, les noirs k."""
        open_h_file = "r3k2r/ppppppp1/8/8/8/8/PPPPPPP1/R3K2R b KQkq - 0 1"
        after = play(open_h_file, "h8h1")
        self.assertEqual(after.castling_rights, frozenset("Qq"))


class TestTheSquaresBetween(unittest.TestCase):
    def test_a_piece_in_the_way_blocks_the_castle(self):
        blocked = "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3KB1R w KQkq - 0 1"
        self.assertNotIn("e1g1", moves_of(blocked))
        self.assertIn("e1c1", moves_of(blocked))

    def test_queenside_needs_b1_empty_too(self):
        blocked = "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/RN2K2R w KQkq - 0 1"
        self.assertNotIn("e1c1", moves_of(blocked))
        self.assertIn("e1g1", moves_of(blocked))


class TestTheSquaresCrossed(unittest.TestCase):
    def test_cannot_castle_out_of_check(self):
        """Tour noire en e-file : le roi est en échec, donc pas de roque."""
        in_check = "4r3/8/8/8/8/8/8/R3K2R w KQ - 0 1"
        self.assertFalse({"e1g1", "e1c1"} & moves_of(in_check))

    def test_cannot_castle_through_an_attacked_square(self):
        """Tour noire en f8, colonne f ouverte : f1 est attaquée."""
        crossed = "r4rk1/ppppp1pp/8/8/8/8/PPPPP1PP/R3K2R w KQ - 0 1"
        self.assertNotIn("e1g1", moves_of(crossed))
        self.assertIn("e1c1", moves_of(crossed))

    def test_the_rook_may_be_attacked(self):
        """Erreur classique : c'est le roi qui doit être en sécurité, pas la tour."""
        rook_attacked = "r3k2r/ppppppp1/8/8/8/8/PPPPPPP1/R3K2R w KQkq - 0 1"
        self.assertIn("e1g1", moves_of(rook_attacked))

    def test_queenside_b1_may_be_attacked(self):
        """b1 doit être vide, pas sûre : le roi passe par d1 et c1, jamais par b1."""
        b_file_open = "1r2k2r/p1pppppp/8/8/8/8/P1PPPPPP/R3K2R w KQk - 0 1"
        self.assertIn("e1c1", moves_of(b_file_open))


if __name__ == "__main__":
    unittest.main()

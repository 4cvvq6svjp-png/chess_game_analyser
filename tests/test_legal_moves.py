"""Le filtre de légalité : un seul endroit, plusieurs bugs réglés d'un coup.

Clouages, fuites du roi et échecs découverts étaient traités séparément, chacun
avec son oubli. Ici ils ne sont plus des cas : ce sont les conséquences d'une
seule règle, « le coup est illégal s'il laisse mon roi en échec ».
"""

import unittest

from chess_engine.game_position import STARTING_FEN
from helpers import (
    Bishop,
    GamePosition,
    King,
    Knight,
    Queen,
    Rook,
    position_with,
    square,
)


def start_position():
    return GamePosition.from_fen(STARTING_FEN)


def play(position, *moves_text):
    """Joue une suite de coups en notation longue ('e2e4'), en les exigeant légaux."""
    for text in moves_text:
        move = next((m for m in position.legal_moves() if str(m) == text), None)
        assert move is not None, f"{text} n'est pas légal dans cette position"
        position = position.apply(move)
    return position


def destinations_from(position, origin):
    return {m.square_to for m in position.legal_moves() if m.square_from == origin}


class TestOpeningCounts(unittest.TestCase):
    def test_twenty_moves_at_the_start(self):
        self.assertEqual(len(start_position().legal_moves()), 20)

    def test_twenty_replies_after_e4(self):
        self.assertEqual(len(play(start_position(), "e2e4").legal_moves()), 20)

    def test_only_the_side_to_move_is_generated(self):
        position = start_position()
        for move in position.legal_moves():
            self.assertEqual(position.piece_at(move.square_from).color, "w")


class TestPinning(unittest.TestCase):
    def test_a_pinned_knight_cannot_move(self):
        position = position_with(
            {"e1": King("w"), "e2": Knight("w"), "e8": Rook("b")}
        )
        self.assertEqual(destinations_from(position, square("e2")), set())

    def test_the_pinned_piece_may_still_take_the_pinner(self):
        position = position_with({"e1": King("w"), "e4": Queen("w"), "e8": Rook("b")})
        destinations = destinations_from(position, square("e4"))
        self.assertIn(square("e8"), destinations)       # prend le cloueur
        self.assertIn(square("e5"), destinations)       # reste sur la ligne
        self.assertNotIn(square("d4"), destinations)    # quitte la ligne : interdit

    def test_an_unpinned_piece_is_unaffected(self):
        position = position_with(
            {"e1": King("w"), "d2": Knight("w"), "e8": Rook("b")}
        )
        self.assertTrue(destinations_from(position, square("d2")))


class TestTheKingIsNoLongerFooled(unittest.TestCase):
    def test_the_king_cannot_slide_along_the_attacking_line(self):
        """Le « king-shadow » : roi en e1, tour en a1. f1 reste sur la ligne.

        L'ancien chemin évaluait la case d'arrivée alors que le roi occupait
        encore e1, qui masquait la tour : f1 semblait sûre. apply() vide la
        case de départ avant le test, donc l'ombre a disparu.
        """
        position = position_with({"e1": King("w"), "a1": Rook("b")})
        destinations = destinations_from(position, square("e1"))
        self.assertNotIn(square("f1"), destinations)
        self.assertNotIn(square("d1"), destinations)
        self.assertEqual(
            destinations, {square("d2"), square("e2"), square("f2")}
        )

    def test_the_king_cannot_step_into_check(self):
        position = position_with({"e1": King("w"), "d8": Rook("b")})
        destinations = destinations_from(position, square("e1"))
        self.assertNotIn(square("d1"), destinations)
        self.assertNotIn(square("d2"), destinations)

    def test_in_check_only_the_answers_remain(self):
        position = position_with(
            {"e1": King("w"), "a2": Rook("w"), "e8": Queen("b")}
        )
        self.assertTrue(position.is_in_check("w"))
        for move in position.legal_moves():
            self.assertFalse(
                position.apply(move).is_in_check("w"), f"{move} laisse le roi en échec"
            )

    def test_a_diagonal_pin_confines_to_the_diagonal(self):
        """Fou en c3, cloué par la dame en a5 : il ne quitte pas a5-e1."""
        position = position_with(
            {"e1": King("w"), "c3": Bishop("w"), "a5": Queen("b")}
        )
        self.assertEqual(
            destinations_from(position, square("c3")),
            {square("a5"), square("b4"), square("d2")},
        )


class TestEnPassantIsGenerated(unittest.TestCase):
    def test_the_capture_appears_after_a_double_push(self):
        position = play(start_position(), "e2e4", "a7a6", "e4e5", "d7d5")
        self.assertEqual(position.en_passant_square, square("d6"))
        self.assertIn("e5d6", {str(m) for m in position.legal_moves()})

    def test_it_is_gone_one_move_later(self):
        position = play(
            start_position(), "e2e4", "a7a6", "e4e5", "d7d5", "a2a3", "a6a5"
        )
        self.assertIsNone(position.en_passant_square)
        self.assertNotIn("e5d6", {str(m) for m in position.legal_moves()})

    def test_the_captured_pawn_leaves_the_board(self):
        position = play(start_position(), "e2e4", "a7a6", "e4e5", "d7d5", "e5d6")
        self.assertIsNone(position.piece_at(square("d5")))
        self.assertEqual(position.piece_at(square("d6")).name, "pawn")


class TestNoMoveLeft(unittest.TestCase):
    def test_fools_mate_leaves_nothing(self):
        """1.f3 e5 2.g4 Qh4# : échec et aucun coup -- c'est un mat."""
        position = play(start_position(), "f2f3", "e7e5", "g2g4", "d8h4")
        self.assertTrue(position.is_in_check("w"))
        self.assertEqual(position.legal_moves(), [])

    def test_stalemate_leaves_nothing_without_check(self):
        """Roi noir en a8, dame blanche en b6 : pas d'échec, pas de coup."""
        position = position_with(
            {"a8": King("b"), "b6": Queen("w"), "h1": King("w")}, side_to_move="b"
        )
        self.assertFalse(position.is_in_check("b"))
        self.assertEqual(position.legal_moves(), [])


if __name__ == "__main__":
    unittest.main()

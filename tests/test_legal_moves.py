"""Le filtre de légalité : un seul endroit, plusieurs bugs réglés d'un coup.

Clouages, fuites du roi et échecs découverts étaient traités séparément dans
``is_it_checkmate`` et ``_can_move``, chacun avec son oubli. Ici ils ne sont
plus des cas : ce sont les conséquences d'une seule règle, « le coup est
illégal s'il laisse mon roi en échec ».
"""

import unittest

from helpers import (
    Board,
    GamePosition,
    King,
    Knight,
    Queen,
    Rook,
    empty_board,
    place,
    square,
)


def start_position():
    return GamePosition.from_board(Board("classic"))


def play(position, *moves_text):
    """Joue une suite de coups en notation longue ('e2e4'), en les exigeant légaux."""
    for text in moves_text:
        move = next(
            (m for m in position.legal_moves() if str(m) == text), None
        )
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
        """Cavalier blanc en e2, roi en e1, tour noire en e8 : il est cloué."""
        board = empty_board()
        place(board, King("w"), square("e1"))
        place(board, Knight("w"), square("e2"))
        place(board, Rook("b"), square("e8"))
        position = GamePosition.from_board(board)

        self.assertEqual(destinations_from(position, square("e2")), set())

    def test_the_pinned_piece_may_still_take_the_pinner(self):
        """Un fou cloué garde le droit de manger celui qui le cloue."""
        board = empty_board()
        place(board, King("w"), square("e1"))
        place(board, Queen("w"), square("e4"))
        place(board, Rook("b"), square("e8"))
        position = GamePosition.from_board(board)

        destinations = destinations_from(position, square("e4"))
        self.assertIn(square("e8"), destinations)       # prend le cloueur
        self.assertIn(square("e5"), destinations)       # reste sur la ligne
        self.assertNotIn(square("d4"), destinations)    # quitte la ligne : interdit

    def test_an_unpinned_piece_is_unaffected(self):
        board = empty_board()
        place(board, King("w"), square("e1"))
        place(board, Knight("w"), square("d2"))
        place(board, Rook("b"), square("e8"))
        position = GamePosition.from_board(board)
        self.assertTrue(destinations_from(position, square("d2")))


class TestTheKingIsNoLongerFooled(unittest.TestCase):
    def test_the_king_cannot_slide_along_the_attacking_line(self):
        """Le « king-shadow » : roi en e1, tour en a1. f1 reste sur la ligne.

        L'ancien chemin évaluait la case d'arrivée alors que le roi occupait
        encore e1, qui masquait la tour : f1 semblait sûre. apply() vide la
        case de départ avant le test, donc l'ombre a disparu.
        """
        board = empty_board()
        place(board, King("w"), square("e1"))
        place(board, Rook("b"), square("a1"))
        position = GamePosition.from_board(board)

        destinations = destinations_from(position, square("e1"))
        self.assertNotIn(square("f1"), destinations)
        self.assertNotIn(square("d1"), destinations)
        self.assertEqual(destinations, {square("d2"), square("e2"), square("f2")})

    def test_the_king_cannot_step_into_check(self):
        board = empty_board()
        place(board, King("w"), square("e1"))
        place(board, Rook("b"), square("d8"))
        position = GamePosition.from_board(board)
        self.assertNotIn(square("d1"), destinations_from(position, square("e1")))
        self.assertNotIn(square("d2"), destinations_from(position, square("e1")))

    def test_in_check_only_the_answers_remain(self):
        """Roi en e1, dame noire en e8 : il faut parer, pas jouer ailleurs."""
        board = empty_board()
        place(board, King("w"), square("e1"))
        place(board, Rook("w"), square("a2"))
        place(board, Queen("b"), square("e8"))
        position = GamePosition.from_board(board)

        self.assertTrue(position.is_in_check("w"))
        for move in position.legal_moves():
            after = position.apply(move)
            self.assertFalse(after.is_in_check("w"), f"{move} laisse le roi en échec")


class TestEnPassantIsGenerated(unittest.TestCase):
    def test_the_capture_appears_after_a_double_push(self):
        position = play(start_position(), "e2e4", "a7a6", "e4e5", "d7d5")
        self.assertEqual(position.en_passant_square, square("d6"))
        self.assertIn("e5d6", {str(m) for m in position.legal_moves()})

    def test_it_is_gone_one_move_later(self):
        position = play(start_position(), "e2e4", "a7a6", "e4e5", "d7d5", "a2a3", "a6a5")
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
        board = empty_board()
        place(board, King("b"), square("a8"))
        place(board, Queen("w"), square("b6"))
        place(board, King("w"), square("h1"))
        position = GamePosition.from_board(board, side_to_move="b")

        self.assertFalse(position.is_in_check("b"))
        self.assertEqual(position.legal_moves(), [])


if __name__ == "__main__":
    unittest.main()

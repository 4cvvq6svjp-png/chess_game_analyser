"""Le coup : notation et immutabilité."""

import unittest

from helpers import Move, square_name


class TestSquareName(unittest.TestCase):
    def test_matches_the_engine_convention(self):
        # row 0 == rangée 8, col 0 == colonne a
        self.assertEqual(square_name((0, 0)), "a8")
        self.assertEqual(square_name((7, 0)), "a1")
        self.assertEqual(square_name((7, 7)), "h1")
        self.assertEqual(square_name((6, 4)), "e2")

    def test_round_trips_with_chess_game_coordinate(self):
        from helpers import chess_game

        game = chess_game("classic")
        for text in ["e2", "a1", "h8", "d5"]:
            square, _ = game.coordinate(f"{text}/{text}")
            self.assertEqual(square_name(square), text)


class TestMove(unittest.TestCase):
    def test_long_notation(self):
        self.assertEqual(str(Move((7, 6), (5, 5))), "g1f3")
        self.assertEqual(str(Move((6, 4), (4, 4))), "e2e4")

    def test_promotion_suffix(self):
        self.assertEqual(str(Move((1, 4), (0, 4), "queen")), "e7e8q")
        self.assertEqual(str(Move((1, 4), (0, 4), "knight")), "e7e8n")

    def test_moves_compare_by_value(self):
        self.assertEqual(Move((6, 4), (4, 4)), Move((6, 4), (4, 4)))
        self.assertNotEqual(Move((6, 4), (4, 4)), Move((6, 4), (5, 4)))
        # utilisable en clé d'ensemble, ce dont le générateur dépend
        self.assertEqual(len({Move((6, 4), (4, 4)), Move((6, 4), (4, 4))}), 1)

    def test_move_is_frozen(self):
        move = Move((6, 4), (4, 4))
        with self.assertRaises(Exception):
            move.square_to = (3, 4)


if __name__ == "__main__":
    unittest.main()

import unittest

from helpers import chess_game


class TestCoordinate(unittest.TestCase):
    def setUp(self):
        self.game = chess_game("classic")

    def test_parses_squares_to_tuples(self):
        start, end = self.game.coordinate("a1/a3")
        self.assertEqual(start, (7, 0))
        self.assertEqual(end, (5, 0))

    def test_parses_other_file(self):
        start, end = self.game.coordinate("e2/e4")
        self.assertEqual(start, (6, 4))
        self.assertEqual(end, (4, 4))

    def test_malformed_input_raises(self):
        with self.assertRaises(Exception):
            self.game.coordinate("not-a-move")


class TestCouldBeAMove(unittest.TestCase):
    def setUp(self):
        self.game = chess_game("classic")  # turn 0 -> white to move

    def test_white_can_select_white_piece(self):
        self.assertTrue(self.game._could_be_a_move((6, 0), (5, 0)))

    def test_white_cannot_select_black_piece(self):
        self.assertFalse(self.game._could_be_a_move((1, 0), (2, 0)))

    def test_empty_start_square(self):
        self.assertFalse(self.game._could_be_a_move((4, 0), (3, 0)))

    def test_same_square_rejected(self):
        self.assertFalse(self.game._could_be_a_move((6, 0), (6, 0)))

    def test_out_of_range_rejected(self):
        self.assertFalse(self.game._could_be_a_move((6, 0), (9, 0)))


if __name__ == "__main__":
    unittest.main()

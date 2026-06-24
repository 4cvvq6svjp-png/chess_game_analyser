import unittest

from helpers import empty_board, place, Knight, Pawn


class TestKnight(unittest.TestCase):
    def setUp(self):
        self.board = empty_board()
        self.knight = place(self.board, Knight("w"), (4, 4))

    def valid(self, to):
        return self.knight._is_valid_move((4, 4), to, self.board)

    def test_legal_L_moves(self):
        for to in [(2, 3), (2, 5), (3, 2), (3, 6), (5, 2), (5, 6), (6, 3), (6, 5)]:
            self.assertTrue(self.valid(to), f"{to} should be a legal knight move")

    def test_diagonal_two_is_rejected(self):
        # regression: the old code accepted (row±2, any non-zero col delta)
        self.assertFalse(self.valid((2, 2)))
        self.assertFalse(self.valid((2, 1)))  # col delta 3
        self.assertFalse(self.valid((6, 6)))

    def test_straight_and_adjacent_rejected(self):
        self.assertFalse(self.valid((2, 4)))  # straight 2
        self.assertFalse(self.valid((4, 6)))  # straight 2 sideways
        self.assertFalse(self.valid((5, 5)))  # one diagonal step

    def test_capture_enemy_ok_friendly_blocked(self):
        place(self.board, Pawn("b"), (2, 5))
        self.assertTrue(self.valid((2, 5)))
        place(self.board, Pawn("w"), (2, 3))
        self.assertFalse(self.valid((2, 3)))


if __name__ == "__main__":
    unittest.main()

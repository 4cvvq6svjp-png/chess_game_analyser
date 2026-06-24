import unittest

from helpers import empty_board, place, Rook, Bishop, Queen, Pawn


class TestRook(unittest.TestCase):
    def setUp(self):
        self.board = empty_board()
        self.rook = place(self.board, Rook("w"), (4, 4))

    def test_straight_moves_valid(self):
        for to in [(4, 0), (4, 7), (0, 4), (7, 4)]:
            self.assertTrue(self.rook._is_valid_move((4, 4), to, self.board))

    def test_diagonal_invalid(self):
        self.assertFalse(self.rook._is_valid_move((4, 4), (2, 2), self.board))

    def test_blocked_path(self):
        place(self.board, Pawn("b"), (4, 2))
        self.assertFalse(self.rook._is_valid_move((4, 4), (4, 0), self.board))

    def test_same_color_landing(self):
        place(self.board, Pawn("w"), (4, 0))
        self.assertFalse(self.rook._is_valid_move((4, 4), (4, 0), self.board))

    def test_capture_enemy(self):
        place(self.board, Pawn("b"), (4, 0))
        self.assertTrue(self.rook._is_valid_move((4, 4), (4, 0), self.board))


class TestBishop(unittest.TestCase):
    def setUp(self):
        self.board = empty_board()
        self.bishop = place(self.board, Bishop("w"), (4, 4))

    def test_diagonal_moves_valid(self):
        for to in [(2, 2), (6, 6), (2, 6), (6, 2)]:
            self.assertTrue(self.bishop._is_valid_move((4, 4), to, self.board))

    def test_straight_invalid(self):
        self.assertFalse(self.bishop._is_valid_move((4, 4), (4, 0), self.board))

    def test_blocked_path(self):
        place(self.board, Pawn("b"), (3, 3))
        self.assertFalse(self.bishop._is_valid_move((4, 4), (2, 2), self.board))


class TestQueen(unittest.TestCase):
    def setUp(self):
        self.board = empty_board()
        self.queen = place(self.board, Queen("w"), (4, 4))

    def test_straight_and_diagonal_valid(self):
        self.assertTrue(self.queen._is_valid_move((4, 4), (4, 0), self.board))
        self.assertTrue(self.queen._is_valid_move((4, 4), (2, 2), self.board))

    def test_knight_shape_invalid(self):
        self.assertFalse(self.queen._is_valid_move((4, 4), (2, 3), self.board))


if __name__ == "__main__":
    unittest.main()

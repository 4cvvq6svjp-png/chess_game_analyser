import unittest

from helpers import empty_board, place, King, Rook, Bishop, Knight, Pawn


class TestIsInCheck(unittest.TestCase):
    def test_no_check_for_lone_kings(self):
        board = empty_board()
        place(board, King("w"), (7, 4))
        place(board, King("b"), (0, 4))
        self.assertFalse(board.is_in_check("w")["check"])

    def test_rook_check_reports_attacker(self):
        board = empty_board()
        place(board, King("w"), (7, 4))
        place(board, Rook("b"), (0, 4))
        result = board.is_in_check("w")
        self.assertTrue(result["check"])
        self.assertFalse(result["double_check"])
        self.assertEqual(result["square_attacker"], (0, 4))

    def test_bishop_check(self):
        board = empty_board()
        place(board, King("w"), (4, 4))
        place(board, Bishop("b"), (1, 1))
        self.assertTrue(board.is_in_check("w")["check"])

    def test_knight_check(self):
        board = empty_board()
        place(board, King("w"), (4, 4))
        place(board, Knight("b"), (2, 3))
        self.assertTrue(board.is_in_check("w")["check"])

    def test_pawn_check(self):
        board = empty_board()
        place(board, King("w"), (4, 4))
        place(board, Pawn("b"), (3, 3))  # black pawn attacks (4,2) and (4,4)
        self.assertTrue(board.is_in_check("w")["check"])

    def test_pawn_in_front_is_not_a_check(self):
        board = empty_board()
        place(board, King("w"), (4, 4))
        place(board, Pawn("b"), (3, 4))  # directly in front, not attacking
        self.assertFalse(board.is_in_check("w")["check"])

    def test_double_check(self):
        board = empty_board()
        place(board, King("w"), (4, 4))
        place(board, Rook("b"), (4, 0))   # along the rank
        place(board, Bishop("b"), (1, 1))  # along the diagonal
        result = board.is_in_check("w")
        self.assertTrue(result["check"])
        self.assertTrue(result["double_check"])

    def test_adjacent_enemy_king_is_check(self):
        # regression for the king-adjacency detection bug
        board = empty_board()
        place(board, King("w"), (4, 4))
        place(board, King("b"), (4, 5))
        self.assertTrue(board.is_in_check("w")["check"])


if __name__ == "__main__":
    unittest.main()

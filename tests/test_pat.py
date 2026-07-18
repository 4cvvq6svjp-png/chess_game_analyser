import unittest

from helpers import empty_board, place, King, Queen


class TestPat(unittest.TestCase):
    def test_stalemate_no_legal_move(self):
        # Black king on a8, not in check, but every square is covered.
        board = empty_board()
        place(board, King("b"), (0, 0))
        place(board, Queen("w"), (2, 1))  # covers (0,1), (1,0), (1,1)
        place(board, King("w"), (7, 7))
        self.assertFalse(board.is_in_check("b")["check"])
        self.assertTrue(board._is_pat("b"))

    def test_not_pat_when_a_move_exists(self):
        board = empty_board()
        place(board, King("b"), (0, 0))
        place(board, King("w"), (7, 7))
        self.assertFalse(board._is_pat("b"))


if __name__ == "__main__":
    unittest.main()

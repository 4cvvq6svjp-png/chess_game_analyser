import unittest

from helpers import empty_board, place, King, Pawn, Rook


class TestKing(unittest.TestCase):
    def test_long_move_rejected(self):
        board = empty_board()
        king = place(board, King("w"), (4, 4))
        self.assertFalse(king._is_valid_move((4, 4), (4, 6), board))

    def test_cannot_step_next_to_enemy_king(self):
        # regression for the `< 1` vs `<= 1` adjacency bug
        board = empty_board()
        wk = place(board, King("w"), (4, 4))
        place(board, King("b"), (4, 6))
        # (4,5) is adjacent to the black king -> illegal
        self.assertFalse(wk._is_valid_move((4, 4), (4, 5), board))
        # (5,4) is two files away from the black king -> legal
        self.assertTrue(wk._is_valid_move((4, 4), (5, 4), board))

    def test_cannot_capture_friendly_piece(self):
        board = empty_board()
        wk = place(board, King("w"), (4, 4))
        place(board, Pawn("w"), (4, 5))
        self.assertFalse(wk._is_valid_move((4, 4), (4, 5), board))

    def test_can_capture_undefended_enemy(self):
        board = empty_board()
        wk = place(board, King("w"), (4, 4))
        place(board, Pawn("b"), (4, 5))
        self.assertTrue(wk._is_valid_move((4, 4), (4, 5), board))

    def test_cannot_move_into_a_rook_attack(self):
        board = empty_board()
        wk = place(board, King("w"), (4, 4))
        place(board, Rook("b"), (0, 5))  # controls the whole file 5
        self.assertFalse(wk._is_valid_move((4, 4), (4, 5), board))


if __name__ == "__main__":
    unittest.main()

import unittest

from helpers import empty_board, place, Pawn


class TestPawnMoves(unittest.TestCase):
    def setUp(self):
        self.board = empty_board()
        # white pawn on its starting rank (rank 2 -> row 6)
        self.pawn = place(self.board, Pawn("w"), (6, 4))

    def test_single_and_double_push(self):
        self.assertTrue(self.pawn._is_valid_move((6, 4), (5, 4), self.board))
        self.assertTrue(self.pawn._is_valid_move((6, 4), (4, 4), self.board))

    def test_push_blocked(self):
        place(self.board, Pawn("b"), (5, 4))
        self.assertFalse(self.pawn._is_valid_move((6, 4), (5, 4), self.board))
        # cannot jump over the blocker on the double push either
        self.assertFalse(self.pawn._is_valid_move((6, 4), (4, 4), self.board))

    def test_double_push_only_from_start(self):
        pawn = place(self.board, Pawn("w"), (5, 0))
        self.assertFalse(pawn._is_valid_move((5, 0), (3, 0), self.board))

    def test_cannot_capture_forward(self):
        place(self.board, Pawn("b"), (5, 4))
        self.assertFalse(self.pawn._is_valid_move((6, 4), (5, 4), self.board))

    def test_diagonal_capture(self):
        place(self.board, Pawn("b"), (5, 3))
        self.assertTrue(self.pawn._is_valid_move((6, 4), (5, 3), self.board))

    def test_diagonal_into_empty_is_not_a_move(self):
        self.assertFalse(self.pawn._is_valid_move((6, 4), (5, 3), self.board))


class TestEnPassant(unittest.TestCase):
    def setUp(self):
        self.board = empty_board()
        # white pawn on rank 5 (row 3), black pawn that just double-pushed beside it
        self.white = place(self.board, Pawn("w"), (3, 4))
        self.black = place(self.board, Pawn("b"), (3, 3))
        self.board.play_stack = [
            {"piece": "pawn", "square_from": (1, 3), "square_to": (3, 3)}
        ]

    def test_en_passant_is_valid(self):
        self.assertTrue(self.white._is_valid_move((3, 4), (2, 3), self.board))

    def test_validation_does_not_mutate_board(self):
        # regression: _is_valid_move used to delete the captured pawn as a side effect
        self.white._is_valid_move((3, 4), (2, 3), self.board)
        self.assertIsNotNone(
            self.board.chessboard[3][3],
            "validation must not remove the en-passant pawn",
        )

    def test_execution_removes_captured_pawn(self):
        self.white._execute_move(self.board, (3, 4), (2, 3))
        self.assertIsNone(self.board.chessboard[3][3], "captured pawn should be gone")
        self.assertIsNone(self.board.chessboard[3][4], "pawn left its origin")
        self.assertIsNotNone(self.board.chessboard[2][3], "pawn landed on the target")

    def test_no_en_passant_without_double_push(self):
        self.board.play_stack = [
            {"piece": "pawn", "square_from": (2, 3), "square_to": (3, 3)}
        ]
        self.assertFalse(self.white._is_valid_move((3, 4), (2, 3), self.board))


class TestPromotionFlag(unittest.TestCase):
    def test_isbackrank_pawn_move(self):
        board = empty_board()
        place(board, Pawn("w"), (1, 4))
        self.assertTrue(board._isbackrank_PawnMove((1, 4), (0, 4)))
        place(board, Pawn("w"), (5, 4))
        self.assertFalse(board._isbackrank_PawnMove((5, 4), (4, 4)))


if __name__ == "__main__":
    unittest.main()

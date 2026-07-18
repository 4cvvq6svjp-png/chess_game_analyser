import unittest

from helpers import empty_board, place, King, Rook, Pawn


def is_mate(board, color):
    """Run is_in_check then is_it_checkmate the way launch_game does."""
    info = board.is_in_check(color)
    if not info["check"]:
        return False
    return board.is_it_checkmate(color, info["square_attacker"], info["double_check"])


class TestCheckmate(unittest.TestCase):
    def test_back_rank_mate(self):
        # Black king boxed on the back rank by its own pawns; white rook checks
        # along rank 0 with no flight square.
        board = empty_board()
        place(board, King("b"), (0, 4))
        place(board, Pawn("b"), (0, 5))   # blocks the far square on the rank
        place(board, Pawn("b"), (1, 3))   # own pawns block the rank-1 escapes
        place(board, Pawn("b"), (1, 4))
        place(board, Pawn("b"), (1, 5))
        place(board, Rook("w"), (0, 0))
        place(board, King("w"), (7, 7))
        self.assertTrue(is_mate(board, "b"))

    def test_orthogonal_escape_is_not_mate(self):
        # regression: the escape scan only looked at diagonal squares, so a king
        # whose only flight square is straight down was wrongly judged mated.
        board = empty_board()
        place(board, King("b"), (0, 4))
        place(board, Pawn("b"), (0, 5))   # kill the on-rank escape
        place(board, Pawn("b"), (1, 3))   # diagonal flight squares blocked
        place(board, Pawn("b"), (1, 5))
        place(board, Rook("w"), (0, 0))
        place(board, King("w"), (7, 7))
        # (1,4) straight down is the only out -> must be seen as not-mate
        self.assertFalse(is_mate(board, "b"))

    def test_check_but_king_can_capture_attacker(self):
        # The only out is the king capturing the undefended checking rook.
        board = empty_board()
        place(board, King("b"), (0, 4))
        place(board, Pawn("b"), (0, 3))   # block remaining flight squares
        place(board, Pawn("b"), (1, 3))
        place(board, Pawn("b"), (1, 4))
        place(board, Pawn("b"), (1, 5))
        place(board, Rook("w"), (0, 5))   # adjacent, undefended
        place(board, King("w"), (7, 7))
        self.assertFalse(is_mate(board, "b"))


if __name__ == "__main__":
    unittest.main()

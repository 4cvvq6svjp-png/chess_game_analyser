"""La position : le conteneur d'état et sa passerelle depuis ``Board``."""

import unittest

from helpers import GamePosition, Knight, Pawn, empty_board, place


def stack_move(board, piece, square_from, square_to):
    """Empile un coup au format de ``Piece._execute_move``."""
    board.play_stack.append(
        {"piece": piece, "square_from": square_from, "square_to": square_to}
    )


class TestGamePosition(unittest.TestCase):
    def test_from_board_copies_the_grid_immutably(self):
        board = empty_board()
        place(board, Knight("w"), (4, 4))
        position = GamePosition.from_board(board)

        self.assertIsInstance(position.board, tuple)
        self.assertIsInstance(position.board[0], tuple)
        # modifier le Board d'origine ne doit plus toucher la position
        board.chessboard[4][4] = None
        self.assertIsNotNone(position.piece_at((4, 4)))

    def test_piece_at_reads_the_grid(self):
        board = empty_board()
        knight = place(board, Knight("b"), (0, 6))
        position = GamePosition.from_board(board)
        self.assertIs(position.piece_at((0, 6)), knight)
        self.assertIsNone(position.piece_at((3, 3)))

    def test_defaults_describe_a_fresh_game(self):
        position = GamePosition.from_board(empty_board())
        self.assertEqual(position.side_to_move, "w")
        self.assertEqual(position.castling_rights, frozenset("KQkq"))
        self.assertEqual(position.halfmove_clock, 0)
        self.assertEqual(position.fullmove_number, 1)

    def test_no_en_passant_square_on_an_empty_stack(self):
        self.assertIsNone(GamePosition.from_board(empty_board()).en_passant_square)

    def test_double_pawn_push_opens_an_en_passant_square(self):
        board = empty_board()
        place(board, Pawn("b"), (3, 4))
        stack_move(board, "pawn", (1, 4), (3, 4))  # e7-e5
        # la case survolée est e6, soit (2, 4)
        self.assertEqual(GamePosition.from_board(board).en_passant_square, (2, 4))

    def test_single_push_opens_nothing(self):
        board = empty_board()
        place(board, Pawn("b"), (2, 4))
        stack_move(board, "pawn", (1, 4), (2, 4))
        self.assertIsNone(GamePosition.from_board(board).en_passant_square)

    def test_a_two_square_non_pawn_move_opens_nothing(self):
        board = empty_board()
        place(board, Knight("w"), (5, 3))
        stack_move(board, "knight", (7, 4), (5, 3))
        self.assertIsNone(GamePosition.from_board(board).en_passant_square)

    def test_position_is_frozen(self):
        position = GamePosition.from_board(empty_board())
        with self.assertRaises(Exception):
            position.side_to_move = "b"


if __name__ == "__main__":
    unittest.main()

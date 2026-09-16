"""Les générateurs des pièces qui glissent : fou, tour, dame.

Même filet que pour le cavalier : sur un échiquier encombré, le générateur et
le validateur historique doivent s'accorder sur les 64 cases d'arrivée.
"""

import unittest

from helpers import (
    Bishop,
    GamePosition,
    Knight,
    Pawn,
    Queen,
    Rook,
    empty_board,
    place,
)

CENTRE = (4, 4)


class SliderCase(unittest.TestCase):
    """Outillage commun aux trois pièces."""

    def destinations(self, piece, board, origin=CENTRE):
        position = GamePosition.from_board(board)
        return {move.square_to for move in piece.pseudo_moves(position, origin)}

    def crowded_board(self, piece):
        """L'échiquier de référence : deux obstacles amis, deux adverses."""
        board = empty_board()
        place(board, piece, CENTRE)
        place(board, Pawn("w"), (2, 2))   # ami, sur la diagonale nord-ouest
        place(board, Pawn("b"), (6, 6))   # adverse, sur la diagonale sud-est
        place(board, Knight("w"), (4, 1))  # ami, sur la ligne
        place(board, Knight("b"), (1, 4))  # adverse, sur la colonne
        return board

    def assert_agrees_with_validator(self, piece, board, origin=CENTRE):
        generated = self.destinations(piece, board, origin)
        # non-vacuité : le test doit comparer des cas des deux bords
        self.assertTrue(0 < len(generated) < 64)
        for row in range(8):
            for col in range(8):
                with self.subTest(square=(row, col)):
                    self.assertEqual(
                        (row, col) in generated,
                        bool(piece._is_valid_move(origin, (row, col), board)),
                    )


class TestBishop(SliderCase):
    def test_free_board_reaches_both_diagonals(self):
        board = empty_board()
        bishop = place(board, Bishop("w"), CENTRE)
        self.assertEqual(len(self.destinations(bishop, board)), 13)

    def test_stops_before_a_friend_and_takes_an_enemy(self):
        board = empty_board()
        bishop = place(board, Bishop("w"), CENTRE)
        place(board, Pawn("w"), (2, 2))
        place(board, Pawn("b"), (6, 6))
        destinations = self.destinations(bishop, board)
        self.assertIn((3, 3), destinations)      # jusqu'à l'ami exclu
        self.assertNotIn((2, 2), destinations)   # l'ami lui-même
        self.assertNotIn((1, 1), destinations)   # au-delà de l'ami
        self.assertIn((6, 6), destinations)      # l'adverse est pris
        self.assertNotIn((7, 7), destinations)   # mais on ne le traverse pas

    def test_agrees_with_validator(self):
        board = self.crowded_board(Bishop("w"))
        self.assert_agrees_with_validator(board.chessboard[4][4], board)


class TestRook(SliderCase):
    def test_free_board_reaches_rank_and_file(self):
        board = empty_board()
        rook = place(board, Rook("w"), CENTRE)
        self.assertEqual(len(self.destinations(rook, board)), 14)

    def test_stops_before_a_friend_and_takes_an_enemy(self):
        board = empty_board()
        rook = place(board, Rook("b"), CENTRE)
        place(board, Pawn("b"), (4, 1))
        place(board, Pawn("w"), (1, 4))
        destinations = self.destinations(rook, board)
        self.assertIn((4, 2), destinations)
        self.assertNotIn((4, 1), destinations)
        self.assertNotIn((4, 0), destinations)
        self.assertIn((1, 4), destinations)
        self.assertNotIn((0, 4), destinations)

    def test_agrees_with_validator(self):
        board = self.crowded_board(Rook("w"))
        self.assert_agrees_with_validator(board.chessboard[4][4], board)


class TestQueen(SliderCase):
    def test_free_board_is_bishop_plus_rook(self):
        board = empty_board()
        queen = place(board, Queen("w"), CENTRE)
        self.assertEqual(len(self.destinations(queen, board)), 27)

    def test_covers_exactly_the_union(self):
        board = empty_board()
        queen = place(board, Queen("w"), CENTRE)
        queen_squares = self.destinations(queen, board)

        board = empty_board()
        bishop = place(board, Bishop("w"), CENTRE)
        bishop_squares = self.destinations(bishop, board)

        board = empty_board()
        rook = place(board, Rook("w"), CENTRE)
        rook_squares = self.destinations(rook, board)

        self.assertEqual(queen_squares, bishop_squares | rook_squares)

    def test_agrees_with_validator(self):
        board = self.crowded_board(Queen("b"))
        self.assert_agrees_with_validator(board.chessboard[4][4], board)


class TestFromACorner(SliderCase):
    def test_rook_in_a_corner_stays_on_the_board(self):
        board = empty_board()
        rook = place(board, Rook("w"), (7, 0))  # a1
        destinations = self.destinations(rook, board, (7, 0))
        self.assertEqual(len(destinations), 14)
        self.assertTrue(all(0 <= r < 8 and 0 <= c < 8 for r, c in destinations))

    def test_bishop_in_a_corner_has_one_diagonal(self):
        board = empty_board()
        bishop = place(board, Bishop("w"), (7, 0))
        self.assertEqual(len(self.destinations(bishop, board, (7, 0))), 7)


if __name__ == "__main__":
    unittest.main()

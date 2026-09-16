"""Le générateur du pion : poussées, prises, en passant, promotion.

C'est la pièce qui s'écarte le plus du schéma des autres : un déplacement peut
produire quatre coups (promotion), et un coup peut dépendre du coup précédent
(en passant). L'équivalence avec ``_is_valid_move`` porte donc sur les cases
d'arrivée, la promotion étant vérifiée à part.
"""

import unittest

from helpers import GamePosition, Knight, Pawn, Queen, empty_board, place


def stack_move(board, piece, square_from, square_to):
    board.play_stack.append(
        {"piece": piece, "square_from": square_from, "square_to": square_to}
    )


class PawnCase(unittest.TestCase):
    def moves(self, pawn, board, origin):
        position = GamePosition.from_board(board)
        return list(pawn.pseudo_moves(position, origin))

    def destinations(self, pawn, board, origin):
        return {move.square_to for move in self.moves(pawn, board, origin)}

    def assert_agrees_with_validator(self, pawn, board, origin):
        generated = self.destinations(pawn, board, origin)
        for row in range(8):
            for col in range(8):
                with self.subTest(square=(row, col)):
                    self.assertEqual(
                        (row, col) in generated,
                        bool(pawn._is_valid_move(origin, (row, col), board)),
                    )


class TestPushes(PawnCase):
    def test_white_advances_one_and_two_from_its_rank(self):
        board = empty_board()
        pawn = place(board, Pawn("w"), (6, 4))  # e2
        self.assertEqual(self.destinations(pawn, board, (6, 4)), {(5, 4), (4, 4)})

    def test_black_advances_downwards(self):
        board = empty_board()
        pawn = place(board, Pawn("b"), (1, 4))  # e7
        self.assertEqual(self.destinations(pawn, board, (1, 4)), {(2, 4), (3, 4)})

    def test_only_one_step_once_it_has_left_its_rank(self):
        board = empty_board()
        pawn = place(board, Pawn("w"), (5, 4))
        self.assertEqual(self.destinations(pawn, board, (5, 4)), {(4, 4)})

    def test_a_piece_in_front_blocks_everything(self):
        board = empty_board()
        pawn = place(board, Pawn("w"), (6, 4))
        place(board, Knight("b"), (5, 4))
        self.assertEqual(self.destinations(pawn, board, (6, 4)), set())

    def test_the_double_step_cannot_jump_over_a_piece(self):
        board = empty_board()
        pawn = place(board, Pawn("w"), (6, 4))
        place(board, Knight("b"), (4, 4))
        self.assertEqual(self.destinations(pawn, board, (6, 4)), {(5, 4)})

    def test_a_pawn_never_captures_straight_ahead(self):
        board = empty_board()
        pawn = place(board, Pawn("w"), (5, 4))
        place(board, Knight("b"), (4, 4))
        self.assertNotIn((4, 4), self.destinations(pawn, board, (5, 4)))


class TestCaptures(PawnCase):
    def test_takes_diagonally_but_not_a_friend(self):
        board = empty_board()
        pawn = place(board, Pawn("w"), (5, 4))
        place(board, Knight("b"), (4, 3))
        place(board, Knight("w"), (4, 5))
        destinations = self.destinations(pawn, board, (5, 4))
        self.assertIn((4, 3), destinations)
        self.assertNotIn((4, 5), destinations)

    def test_an_empty_diagonal_is_not_a_move(self):
        board = empty_board()
        pawn = place(board, Pawn("w"), (5, 4))
        self.assertEqual(self.destinations(pawn, board, (5, 4)), {(4, 4)})

    def test_edge_file_does_not_wrap_around(self):
        board = empty_board()
        pawn = place(board, Pawn("w"), (5, 0))  # colonne a
        for row, col in self.destinations(pawn, board, (5, 0)):
            self.assertTrue(0 <= col < 8)
            self.assertLessEqual(abs(col - 0), 1)


class TestEnPassant(PawnCase):
    def setUp(self):
        """Noir vient de jouer e7-e5 ; un pion blanc attend en d5."""
        self.board = empty_board()
        self.pawn = place(self.board, Pawn("w"), (3, 3))  # d5
        place(self.board, Pawn("b"), (3, 4))              # e5, le pion à prendre
        stack_move(self.board, "pawn", (1, 4), (3, 4))

    def test_the_capture_is_generated(self):
        self.assertIn((2, 4), self.destinations(self.pawn, self.board, (3, 3)))

    def test_it_disappears_if_the_pawn_came_in_two_steps(self):
        self.board.play_stack = []
        stack_move(self.board, "pawn", (2, 4), (3, 4))
        self.assertNotIn((2, 4), self.destinations(self.pawn, self.board, (3, 3)))

    def test_it_disappears_without_a_pawn_to_take(self):
        self.board.chessboard[3][4] = None
        self.assertNotIn((2, 4), self.destinations(self.pawn, self.board, (3, 3)))

    def test_agrees_with_the_validator(self):
        self.assert_agrees_with_validator(self.pawn, self.board, (3, 3))


class TestPromotion(PawnCase):
    def test_reaching_the_back_rank_offers_four_pieces(self):
        board = empty_board()
        pawn = place(board, Pawn("w"), (1, 4))  # e7
        moves = self.moves(pawn, board, (1, 4))
        self.assertEqual(len(moves), 4)
        self.assertEqual(
            {move.promotion for move in moves},
            {"queen", "rook", "bishop", "knight"},
        )
        self.assertEqual({move.square_to for move in moves}, {(0, 4)})

    def test_a_capture_onto_the_back_rank_promotes_too(self):
        board = empty_board()
        pawn = place(board, Pawn("w"), (1, 4))
        place(board, Queen("b"), (0, 5))
        place(board, Queen("b"), (0, 4))  # bloque la poussée
        moves = self.moves(pawn, board, (1, 4))
        self.assertEqual({move.square_to for move in moves}, {(0, 5)})
        self.assertEqual(len(moves), 4)

    def test_black_promotes_on_the_first_row(self):
        board = empty_board()
        pawn = place(board, Pawn("b"), (6, 4))
        moves = self.moves(pawn, board, (6, 4))
        self.assertEqual({move.square_to for move in moves}, {(7, 4)})
        self.assertEqual(len(moves), 4)

    def test_promotion_names_match_create_piece_by_name(self):
        from helpers import Board

        for name in Pawn.PROMOTION_CHOICES:
            piece = Board.create_piece_by_name(name, "w")
            self.assertIsNotNone(piece, f"{name} doit être constructible")
            self.assertEqual(piece.name, name)

    def test_an_ordinary_move_carries_no_promotion(self):
        board = empty_board()
        pawn = place(board, Pawn("w"), (6, 4))
        self.assertTrue(all(m.promotion is None for m in self.moves(pawn, board, (6, 4))))


class TestAgreesWithValidator(PawnCase):
    def test_on_a_crowded_board(self):
        board = empty_board()
        pawn = place(board, Pawn("w"), (6, 4))
        place(board, Knight("b"), (5, 3))
        place(board, Knight("w"), (5, 5))
        self.assert_agrees_with_validator(pawn, board, (6, 4))

    def test_when_promoting(self):
        board = empty_board()
        pawn = place(board, Pawn("w"), (1, 4))
        place(board, Queen("b"), (0, 5))
        self.assert_agrees_with_validator(pawn, board, (1, 4))

    def test_for_black(self):
        board = empty_board()
        pawn = place(board, Pawn("b"), (1, 4))
        place(board, Knight("w"), (2, 5))
        self.assert_agrees_with_validator(pawn, board, (1, 4))


if __name__ == "__main__":
    unittest.main()

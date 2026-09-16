"""Le générateur de coups du cavalier.

Le test qui compte vraiment est ``test_agrees_with_is_valid_move`` : tant que
les deux chemins coexistent, le nouveau doit dire exactement ce que dit
l'ancien, qui lui est déjà couvert par la suite existante.
"""

import unittest

from helpers import GamePosition, Knight, Move, Pawn, empty_board, place


def position_of(board, side_to_move="w"):
    return GamePosition.from_board(board, side_to_move)


class TestKnightPseudoMoves(unittest.TestCase):
    def setUp(self):
        self.board = empty_board()
        self.knight = place(self.board, Knight("w"), (4, 4))

    def destinations(self, square=(4, 4)):
        moves = self.knight.pseudo_moves(position_of(self.board), square)
        return {move.square_to for move in moves}

    def test_centre_produces_the_eight_jumps(self):
        self.assertEqual(
            self.destinations(),
            {(2, 3), (2, 5), (3, 2), (3, 6), (5, 2), (5, 6), (6, 3), (6, 5)},
        )

    def test_corner_is_clipped_to_the_board(self):
        board = empty_board()
        knight = place(board, Knight("w"), (7, 0))  # a1
        moves = list(knight.pseudo_moves(position_of(board), (7, 0)))
        self.assertEqual({m.square_to for m in moves}, {(5, 1), (6, 2)})

    def test_friendly_blocks_and_enemy_is_capturable(self):
        place(self.board, Pawn("w"), (2, 3))
        place(self.board, Pawn("b"), (2, 5))
        destinations = self.destinations()
        self.assertNotIn((2, 3), destinations)
        self.assertIn((2, 5), destinations)

    def test_never_leaves_the_board(self):
        for row in range(8):
            for col in range(8):
                board = empty_board()
                knight = place(board, Knight("b"), (row, col))
                for move in knight.pseudo_moves(position_of(board), (row, col)):
                    r, c = move.square_to
                    self.assertTrue(
                        0 <= r < 8 and 0 <= c < 8,
                        f"depuis {(row, col)} : {move.square_to} est hors échiquier",
                    )

    def test_yields_move_objects_anchored_on_the_origin(self):
        moves = list(self.knight.pseudo_moves(position_of(self.board), (4, 4)))
        self.assertTrue(all(isinstance(m, Move) for m in moves))
        self.assertTrue(all(m.square_from == (4, 4) for m in moves))
        self.assertTrue(all(m.promotion is None for m in moves))

    def test_agrees_with_is_valid_move(self):
        """Le générateur et le validateur doivent couvrir le même ensemble.

        Sur un échiquier encombré, pour chacune des 64 cases d'arrivée
        possibles : produite par ``pseudo_moves`` si et seulement si
        ``_is_valid_move`` l'accepte.
        """
        place(self.board, Pawn("w"), (2, 3))  # ami, bloque
        place(self.board, Pawn("b"), (2, 5))  # ennemi, capturable
        place(self.board, Pawn("w"), (5, 2))  # ami, bloque
        place(self.board, Pawn("b"), (3, 6))  # ennemi, capturable

        generated = self.destinations()
        for row in range(8):
            for col in range(8):
                accepted = self.knight._is_valid_move((4, 4), (row, col), self.board)
                self.assertEqual(
                    (row, col) in generated,
                    bool(accepted),
                    f"désaccord sur {(row, col)} : "
                    f"généré={(row, col) in generated}, validé={bool(accepted)}",
                )


if __name__ == "__main__":
    unittest.main()

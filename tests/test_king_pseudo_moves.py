"""Le générateur du roi, et l'écart assumé avec son validateur.

Les autres pièces ont un générateur qui décrit exactement ce que décrit leur
``_is_valid_move``. Le roi, non : son validateur refuse en plus les cases
attaquées. Ces tests fixent cet écart plutôt que de le subir -- c'est lui qui
justifie de sortir le filtre des pièces.
"""

import unittest

from helpers import GamePosition, King, Knight, Pawn, Rook, empty_board, place

CENTRE = (4, 4)
NEIGHBOURS = {(3, 3), (3, 4), (3, 5), (4, 3), (4, 5), (5, 3), (5, 4), (5, 5)}


class KingCase(unittest.TestCase):
    def destinations(self, king, board, origin=CENTRE):
        position = GamePosition.from_board(board)
        return {move.square_to for move in king.pseudo_moves(position, origin)}

    def validated(self, king, board, origin=CENTRE):
        return {
            (row, col)
            for row in range(8)
            for col in range(8)
            if king._is_valid_move(origin, (row, col), board)
        }


class TestKingGeometry(KingCase):
    def test_centre_produces_the_eight_neighbours(self):
        board = empty_board()
        king = place(board, King("w"), CENTRE)
        self.assertEqual(self.destinations(king, board), NEIGHBOURS)

    def test_corner_is_clipped(self):
        board = empty_board()
        king = place(board, King("w"), (7, 0))  # a1
        self.assertEqual(
            self.destinations(king, board, (7, 0)), {(6, 0), (6, 1), (7, 1)}
        )

    def test_friendly_blocks_and_enemy_is_capturable(self):
        board = empty_board()
        king = place(board, King("w"), CENTRE)
        place(board, Pawn("w"), (3, 4))
        place(board, Pawn("b"), (5, 4))
        destinations = self.destinations(king, board)
        self.assertNotIn((3, 4), destinations)
        self.assertIn((5, 4), destinations)

    def test_never_moves_two_squares(self):
        board = empty_board()
        king = place(board, King("b"), CENTRE)
        for row, col in self.destinations(king, board):
            self.assertLessEqual(max(abs(row - 4), abs(col - 4)), 1)


class TestKingDivergesFromValidator(KingCase):
    """Le générateur produit un sur-ensemble, et l'écart est mesurable."""

    def test_generator_contains_everything_the_validator_accepts(self):
        board = empty_board()
        king = place(board, King("w"), CENTRE)
        place(board, Rook("b"), (0, 3))       # tour adverse sur la colonne d
        place(board, Knight("b"), (2, 5))     # cavalier adverse, couvre d'autres cases
        self.assertTrue(
            self.validated(king, board) <= self.destinations(king, board),
            "le générateur doit être un sur-ensemble du validateur",
        )

    def test_the_difference_is_exactly_the_attacked_squares(self):
        board = empty_board()
        king = place(board, King("w"), CENTRE)
        place(board, Rook("b"), (0, 3))  # d8 : tient toute la colonne 3

        generated = self.destinations(king, board)
        validated = self.validated(king, board)

        self.assertEqual(generated, NEIGHBOURS)
        # les trois voisines situées sur la colonne de la tour
        self.assertEqual(generated - validated, {(3, 3), (4, 3), (5, 3)})
        self.assertLess(len(validated), len(generated))

    def test_on_a_quiet_board_the_two_agree(self):
        """Sans pièce adverse, le filtre du validateur ne retire rien."""
        board = empty_board()
        king = place(board, King("w"), CENTRE)
        self.assertEqual(self.destinations(king, board), self.validated(king, board))


if __name__ == "__main__":
    unittest.main()

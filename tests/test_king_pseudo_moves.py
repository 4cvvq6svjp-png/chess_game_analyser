"""Le générateur du roi : la géométrie seule.

Le roi produit ses huit pas sans se demander si la case d'arrivée est
attaquée. Ce tri appartient à ``legal_moves()``, et c'est ce qui a fait
disparaître le « king-shadow » -- voir test_legal_moves.
"""

import unittest

from helpers import King, Pawn, Rook, position_with, square

CENTRE = square("e4")
NEIGHBOURS = {square(name) for name in ["d5", "e5", "f5", "d4", "f4", "d3", "e3", "f3"]}


class KingCase(unittest.TestCase):
    def destinations(self, position, origin=CENTRE):
        piece = position.piece_at(origin)
        return {move.square_to for move in piece.pseudo_moves(position, origin)}


class TestKingGeometry(KingCase):
    def test_centre_produces_the_eight_neighbours(self):
        self.assertEqual(
            self.destinations(position_with({"e4": King("w")})), NEIGHBOURS
        )

    def test_corner_is_clipped(self):
        position = position_with({"a1": King("w")})
        self.assertEqual(
            self.destinations(position, square("a1")),
            {square("a2"), square("b2"), square("b1")},
        )

    def test_friendly_blocks_and_enemy_is_capturable(self):
        position = position_with({"e4": King("w"), "e5": Pawn("w"), "e3": Pawn("b")})
        destinations = self.destinations(position)
        self.assertNotIn(square("e5"), destinations)
        self.assertIn(square("e3"), destinations)

    def test_never_moves_two_squares(self):
        position = position_with({"e4": King("b")}, side_to_move="b")
        row, col = CENTRE
        for r, c in self.destinations(position):
            self.assertLessEqual(max(abs(r - row), abs(c - col)), 1)

    def test_attacked_squares_are_still_produced(self):
        """« Pseudo » veut dire sans filtre : la tour adverse ne retire rien ici."""
        position = position_with({"e4": King("w"), "d8": Rook("b")})
        self.assertEqual(self.destinations(position), NEIGHBOURS)
        self.assertIn(square("d5"), self.destinations(position))

    def test_castling_is_not_produced_by_the_king(self):
        """Le roque déplace deux pièces : il vient de la position, pas du roi."""
        position = position_with(
            {"e1": King("w"), "h1": Rook("w"), "a1": Rook("w")}, castling="KQ"
        )
        destinations = self.destinations(position, square("e1"))
        self.assertNotIn(square("g1"), destinations)
        self.assertNotIn(square("c1"), destinations)


if __name__ == "__main__":
    unittest.main()

"""Le générateur de coups du cavalier."""

import unittest

from helpers import Knight, Move, Pawn, position_with, square, square_name

CENTRE = square("e4")


class TestKnightPseudoMoves(unittest.TestCase):
    def destinations(self, position, origin=CENTRE):
        piece = position.piece_at(origin)
        return {move.square_to for move in piece.pseudo_moves(position, origin)}

    def test_centre_produces_the_eight_jumps(self):
        position = position_with({"e4": Knight("w")})
        self.assertEqual(
            self.destinations(position),
            {square(name) for name in ["d6", "f6", "c5", "g5", "c3", "g3", "d2", "f2"]},
        )

    def test_corner_is_clipped_to_the_board(self):
        position = position_with({"a1": Knight("w")})
        self.assertEqual(
            self.destinations(position, square("a1")),
            {square("b3"), square("c2")},
        )

    def test_friendly_blocks_and_enemy_is_capturable(self):
        position = position_with(
            {"e4": Knight("w"), "d6": Pawn("w"), "f6": Pawn("b")}
        )
        destinations = self.destinations(position)
        self.assertNotIn(square("d6"), destinations)
        self.assertIn(square("f6"), destinations)

    def test_never_leaves_the_board(self):
        for row in range(8):
            for col in range(8):
                name = square_name((row, col))
                with self.subTest(origin=name):
                    position = position_with({name: Knight("b")}, side_to_move="b")
                    for destination in self.destinations(position, (row, col)):
                        r, c = destination
                        self.assertTrue(
                            0 <= r < 8 and 0 <= c < 8,
                            f"depuis {name} : {destination} est hors échiquier",
                        )

    def test_yields_move_objects_anchored_on_the_origin(self):
        position = position_with({"e4": Knight("w")})
        moves = list(position.piece_at(CENTRE).pseudo_moves(position, CENTRE))
        self.assertTrue(all(isinstance(m, Move) for m in moves))
        self.assertTrue(all(m.square_from == CENTRE for m in moves))
        self.assertTrue(all(m.promotion is None for m in moves))

    def test_a_knight_ignores_what_stands_between(self):
        """Le cavalier saute : les pièces intermédiaires ne le gênent pas."""
        surrounded = {f"{file}{rank}": Pawn("w") for file in "def" for rank in "345"}
        surrounded["e4"] = Knight("w")
        position = position_with(surrounded)
        self.assertEqual(len(self.destinations(position)), 8)


if __name__ == "__main__":
    unittest.main()

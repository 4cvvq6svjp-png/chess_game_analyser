"""Les générateurs des pièces qui glissent : fou, tour, dame."""

import unittest

from helpers import Bishop, Knight, Pawn, Queen, Rook, position_with, square

CENTRE = square("e4")


class SliderCase(unittest.TestCase):
    def destinations(self, position, origin=CENTRE):
        piece = position.piece_at(origin)
        return {move.square_to for move in piece.pseudo_moves(position, origin)}

    def crowded(self, piece):
        """Deux obstacles amis, deux adverses, autour de la case centrale."""
        return position_with({
            "e4": piece,
            "c6": Pawn("w"),      # ami, diagonale nord-ouest
            "g2": Pawn("b"),      # adverse, diagonale sud-est
            "b4": Knight("w"),    # ami, sur la ligne
            "e7": Knight("b"),    # adverse, sur la colonne
        })


class TestBishop(SliderCase):
    def test_free_board_reaches_both_diagonals(self):
        self.assertEqual(len(self.destinations(position_with({"e4": Bishop("w")}))), 13)

    def test_stops_before_a_friend_and_takes_an_enemy(self):
        position = position_with({"e4": Bishop("w"), "c6": Pawn("w"), "g2": Pawn("b")})
        destinations = self.destinations(position)
        self.assertIn(square("d5"), destinations)      # jusqu'à l'ami exclu
        self.assertNotIn(square("c6"), destinations)   # l'ami lui-même
        self.assertNotIn(square("b7"), destinations)   # au-delà de l'ami
        self.assertIn(square("g2"), destinations)      # l'adverse est pris
        self.assertNotIn(square("h1"), destinations)   # mais on ne le traverse pas

    def test_ignores_the_ranks_and_files(self):
        destinations = self.destinations(self.crowded(Bishop("w")))
        self.assertNotIn(square("e7"), destinations)
        self.assertNotIn(square("b4"), destinations)

    def test_in_a_corner_it_has_one_diagonal(self):
        position = position_with({"a1": Bishop("w")})
        self.assertEqual(len(self.destinations(position, square("a1"))), 7)


class TestRook(SliderCase):
    def test_free_board_reaches_rank_and_file(self):
        self.assertEqual(len(self.destinations(position_with({"e4": Rook("w")}))), 14)

    def test_stops_before_a_friend_and_takes_an_enemy(self):
        position = position_with({"e4": Rook("b"), "b4": Pawn("b"), "e7": Pawn("w")})
        destinations = self.destinations(position)
        self.assertIn(square("c4"), destinations)
        self.assertNotIn(square("b4"), destinations)
        self.assertNotIn(square("a4"), destinations)
        self.assertIn(square("e7"), destinations)
        self.assertNotIn(square("e8"), destinations)

    def test_ignores_the_diagonals(self):
        destinations = self.destinations(self.crowded(Rook("w")))
        self.assertNotIn(square("c6"), destinations)
        self.assertNotIn(square("g2"), destinations)

    def test_in_a_corner_it_still_has_fourteen(self):
        position = position_with({"a1": Rook("w")})
        destinations = self.destinations(position, square("a1"))
        self.assertEqual(len(destinations), 14)
        self.assertTrue(all(0 <= r < 8 and 0 <= c < 8 for r, c in destinations))


class TestQueen(SliderCase):
    def test_free_board_is_bishop_plus_rook(self):
        self.assertEqual(len(self.destinations(position_with({"e4": Queen("w")}))), 27)

    def test_covers_exactly_the_union(self):
        queen = self.destinations(position_with({"e4": Queen("w")}))
        bishop = self.destinations(position_with({"e4": Bishop("w")}))
        rook = self.destinations(position_with({"e4": Rook("w")}))
        self.assertEqual(queen, bishop | rook)

    def test_it_is_blocked_the_same_way_on_both(self):
        destinations = self.destinations(self.crowded(Queen("b")))
        self.assertIn(square("c6"), destinations)      # ami des blancs : capturable
        self.assertIn(square("b4"), destinations)
        self.assertNotIn(square("g2"), destinations)   # pion noir ami : bloqué
        self.assertNotIn(square("e7"), destinations)


if __name__ == "__main__":
    unittest.main()

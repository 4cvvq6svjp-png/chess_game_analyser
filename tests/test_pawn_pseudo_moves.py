"""Le générateur du pion : poussées, prises, en passant, promotion.

C'est la pièce qui s'écarte le plus du schéma des autres : un déplacement peut
produire quatre coups (promotion), et un coup peut dépendre du coup précédent
(en passant, que la position porte dans ``en_passant_square``).
"""

import unittest

from helpers import Knight, Pawn, Queen, position_with, square


class PawnCase(unittest.TestCase):
    def moves(self, position, origin):
        return list(position.piece_at(origin).pseudo_moves(position, origin))

    def destinations(self, position, origin):
        return {move.square_to for move in self.moves(position, origin)}


class TestPushes(PawnCase):
    def test_white_advances_one_and_two_from_its_rank(self):
        position = position_with({"e2": Pawn("w")})
        self.assertEqual(
            self.destinations(position, square("e2")), {square("e3"), square("e4")}
        )

    def test_black_advances_downwards(self):
        position = position_with({"e7": Pawn("b")}, side_to_move="b")
        self.assertEqual(
            self.destinations(position, square("e7")), {square("e6"), square("e5")}
        )

    def test_only_one_step_once_it_has_left_its_rank(self):
        position = position_with({"e3": Pawn("w")})
        self.assertEqual(self.destinations(position, square("e3")), {square("e4")})

    def test_a_piece_in_front_blocks_everything(self):
        position = position_with({"e2": Pawn("w"), "e3": Knight("b")})
        self.assertEqual(self.destinations(position, square("e2")), set())

    def test_the_double_step_cannot_jump_over_a_piece(self):
        position = position_with({"e2": Pawn("w"), "e4": Knight("b")})
        self.assertEqual(self.destinations(position, square("e2")), {square("e3")})

    def test_a_pawn_never_captures_straight_ahead(self):
        position = position_with({"e3": Pawn("w"), "e4": Knight("b")})
        self.assertNotIn(square("e4"), self.destinations(position, square("e3")))


class TestCaptures(PawnCase):
    def test_takes_diagonally_but_not_a_friend(self):
        position = position_with(
            {"e3": Pawn("w"), "d4": Knight("b"), "f4": Knight("w")}
        )
        destinations = self.destinations(position, square("e3"))
        self.assertIn(square("d4"), destinations)
        self.assertNotIn(square("f4"), destinations)

    def test_an_empty_diagonal_is_not_a_move(self):
        position = position_with({"e3": Pawn("w")})
        self.assertEqual(self.destinations(position, square("e3")), {square("e4")})

    def test_edge_file_does_not_wrap_around(self):
        position = position_with({"a3": Pawn("w")})
        for _, col in self.destinations(position, square("a3")):
            self.assertLessEqual(col, 1)


class TestEnPassant(PawnCase):
    def position(self, **kwargs):
        """Noir vient de jouer e7-e5 ; un pion blanc attend en d5."""
        pieces = {"d5": Pawn("w"), "e5": Pawn("b")}
        pieces.update(kwargs.pop("pieces", {}))
        return position_with(pieces, en_passant=kwargs.pop("en_passant", "e6"), **kwargs)

    def test_the_capture_is_generated(self):
        self.assertIn(
            square("e6"), self.destinations(self.position(), square("d5"))
        )

    def test_it_disappears_without_the_en_passant_square(self):
        position = self.position(en_passant="-")
        self.assertNotIn(square("e6"), self.destinations(position, square("d5")))

    def test_it_disappears_without_a_pawn_to_take(self):
        """La case est ouverte mais le pion n'y est pas : pas de prise."""
        position = position_with({"d5": Pawn("w")}, en_passant="e6")
        self.assertNotIn(square("e6"), self.destinations(position, square("d5")))

    def test_the_victim_must_be_an_enemy_pawn(self):
        position = position_with(
            {"d5": Pawn("w"), "e5": Knight("b")}, en_passant="e6"
        )
        self.assertNotIn(square("e6"), self.destinations(position, square("d5")))


class TestPromotion(PawnCase):
    def test_reaching_the_back_rank_offers_four_pieces(self):
        position = position_with({"e7": Pawn("w")})
        moves = self.moves(position, square("e7"))
        self.assertEqual(len(moves), 4)
        self.assertEqual(
            {move.promotion for move in moves},
            {"queen", "rook", "bishop", "knight"},
        )
        self.assertEqual({move.square_to for move in moves}, {square("e8")})

    def test_a_capture_onto_the_back_rank_promotes_too(self):
        position = position_with(
            {"e7": Pawn("w"), "f8": Queen("b"), "e8": Queen("b")}
        )
        moves = self.moves(position, square("e7"))
        self.assertEqual({move.square_to for move in moves}, {square("f8")})
        self.assertEqual(len(moves), 4)

    def test_black_promotes_on_the_first_row(self):
        position = position_with({"e2": Pawn("b")}, side_to_move="b")
        moves = self.moves(position, square("e2"))
        self.assertEqual({move.square_to for move in moves}, {square("e1")})
        self.assertEqual(len(moves), 4)

    def test_an_ordinary_move_carries_no_promotion(self):
        position = position_with({"e2": Pawn("w")})
        self.assertTrue(
            all(m.promotion is None for m in self.moves(position, square("e2")))
        )


if __name__ == "__main__":
    unittest.main()

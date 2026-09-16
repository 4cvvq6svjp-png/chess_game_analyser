"""perft : la conjonction de toutes les règles, comparée à des valeurs publiées.

Un écart d'une unité sur perft(4) -- 197 281 nœuds -- signale une règle fausse
quelque part dans l'arbre, sans dire laquelle : ``perft_divide`` sert alors à
descendre jusqu'au coup fautif.

Ce que ces chiffres couvrent depuis la position initiale : déplacements,
prises, clouages, échecs découverts, sorties d'échec, et la prise en passant,
qui apparaît dès la profondeur 3. Ce qu'ils ne couvrent *pas* : le roque et la
promotion, hors d'atteinte en si peu de coups. Les valider demande une
position de départ arbitraire, donc la FEN, et le roque lui-même.
"""

import os
import unittest

from chess_engine.perft import perft, perft_divide
from helpers import Board, GamePosition

#: Valeurs de référence pour la position initiale, publiées et universellement
#: reprises (Chess Programming Wiki, suites de tests des moteurs).
STARTPOS_NODES = {0: 1, 1: 20, 2: 400, 3: 8902, 4: 197281}

SLOW = os.environ.get("CHESS_SLOW_TESTS")


def start_position():
    return GamePosition.from_board(Board("classic"))


class TestPerftFromTheStart(unittest.TestCase):
    def test_depth_zero_counts_the_position_itself(self):
        self.assertEqual(perft(start_position(), 0), STARTPOS_NODES[0])

    def test_shallow_depths_match_the_published_values(self):
        position = start_position()
        for depth in (1, 2, 3):
            with self.subTest(depth=depth):
                self.assertEqual(perft(position, depth), STARTPOS_NODES[depth])

    @unittest.skipUnless(SLOW, "lent (~4 s) : régler CHESS_SLOW_TESTS pour l'activer")
    def test_depth_four_matches_too(self):
        self.assertEqual(perft(start_position(), 4), STARTPOS_NODES[4])


class TestPerftDivide(unittest.TestCase):
    def test_divide_sums_back_to_the_total(self):
        position = start_position()
        self.assertEqual(sum(perft_divide(position, 3).values()), STARTPOS_NODES[3])

    def test_divide_lists_every_first_move(self):
        divided = perft_divide(start_position(), 2)
        self.assertEqual(len(divided), STARTPOS_NODES[1])
        # depuis la position initiale, chaque premier coup blanc laisse
        # exactement vingt réponses : 20 x 20 = 400
        self.assertEqual(set(divided.values()), {20})

    def test_divide_is_keyed_by_long_notation(self):
        divided = perft_divide(start_position(), 1)
        self.assertIn("e2e4", divided)
        self.assertIn("g1f3", divided)
        self.assertEqual(divided["e2e4"], 1)


class TestPerftIsSensitive(unittest.TestCase):
    """Le compte doit réagir à la position, sinon il ne prouve rien."""

    def test_a_different_position_gives_a_different_count(self):
        position = start_position()
        after_e4 = position.apply(
            next(m for m in position.legal_moves() if str(m) == "e2e4")
        )
        self.assertNotEqual(perft(after_e4, 2), perft(position, 2))


if __name__ == "__main__":
    unittest.main()

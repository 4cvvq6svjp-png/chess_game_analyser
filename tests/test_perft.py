"""perft : la conjonction de toutes les règles, comparée aux valeurs publiées.

Six positions de référence, reprises du Chess Programming Wiki. Chacune vise
un angle mort : la position initiale ne peut pas atteindre le roque ni la
promotion en quelques coups, Kiwipete rend les quatre roques disponibles au
premier coup, les positions 4 et 5 sont remplies de pions prêts à promouvoir,
la 3 est une finale dépouillée où chaque coup compte.

Un écart d'une seule unité signale une règle fausse quelque part dans l'arbre
sans dire laquelle : ``perft_divide`` sert alors à descendre jusqu'au coup
fautif, un demi-coup à la fois.

Les profondeurs sont réparties en deux étages. Tout ce qui reste sous la
seconde tourne par défaut ; le reste attend ``CHESS_SLOW_TESTS``, que la CI
règle.
"""

import os
import unittest

from chess_engine.perft import perft, perft_divide
from helpers import GamePosition

#: Position -> (FEN, noeuds attendus aux profondeurs 1, 2, 3, 4).
#: Valeurs vérifiées sur https://www.chessprogramming.org/Perft_Results
REFERENCE = {
    "initiale": (
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        (20, 400, 8902, 197281),
    ),
    "kiwipete": (
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq -",
        (48, 2039, 97862, 4085603),
    ),
    "position 3": (
        "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
        (14, 191, 2812, 43238),
    ),
    "position 4": (
        "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1",
        (6, 264, 9467, 422333),
    ),
    "position 5": (
        "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8",
        (44, 1486, 62379, 2103487),
    ),
    "position 6": (
        "r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10",
        (46, 2079, 89890, 3894594),
    ),
}

#: Profondeur 4 sur ces positions seulement : les autres demandent plus d'une
#: minute en Python pur, ce qui n'a pas sa place dans une CI de routine.
DEEP_ENOUGH = ("initiale", "position 3", "position 4")

SLOW = os.environ.get("CHESS_SLOW_TESTS")
SLOW_REASON = "lent (~15 s) : régler CHESS_SLOW_TESTS pour l'activer"


def position(name):
    return GamePosition.from_fen(REFERENCE[name][0])


def expected(name, depth):
    return REFERENCE[name][1][depth - 1]


class TestShallowPerft(unittest.TestCase):
    """Ce qui tourne à chaque exécution : les six positions, deux demi-coups."""

    def test_depth_one_and_two_everywhere(self):
        for name in REFERENCE:
            start = position(name)
            for depth in (1, 2):
                with self.subTest(position=name, depth=depth):
                    self.assertEqual(perft(start, depth), expected(name, depth))

    def test_depth_three_from_the_start(self):
        self.assertEqual(perft(position("initiale"), 3), expected("initiale", 3))

    def test_depth_zero_counts_the_position_itself(self):
        self.assertEqual(perft(position("initiale"), 0), 1)


@unittest.skipUnless(SLOW, SLOW_REASON)
class TestDeepPerft(unittest.TestCase):
    """L'étage qui prouve vraiment les règles : roque, promotion, en passant."""

    def test_depth_three_everywhere(self):
        for name in REFERENCE:
            with self.subTest(position=name):
                self.assertEqual(perft(position(name), 3), expected(name, 3))

    def test_depth_four_where_it_is_affordable(self):
        for name in DEEP_ENOUGH:
            with self.subTest(position=name):
                self.assertEqual(perft(position(name), 4), expected(name, 4))


class TestPerftDivide(unittest.TestCase):
    def test_divide_sums_back_to_the_total(self):
        start = position("initiale")
        self.assertEqual(sum(perft_divide(start, 3).values()), expected("initiale", 3))

    def test_divide_lists_every_first_move(self):
        divided = perft_divide(position("initiale"), 2)
        self.assertEqual(len(divided), expected("initiale", 1))
        # depuis la position initiale, chaque premier coup blanc laisse
        # exactement vingt réponses : 20 x 20 = 400
        self.assertEqual(set(divided.values()), {20})

    def test_divide_is_keyed_by_long_notation(self):
        divided = perft_divide(position("initiale"), 1)
        self.assertIn("e2e4", divided)
        self.assertIn("g1f3", divided)
        self.assertEqual(divided["e2e4"], 1)

    def test_divide_reports_the_castles_in_kiwipete(self):
        divided = perft_divide(position("kiwipete"), 1)
        self.assertIn("e1g1", divided)
        self.assertIn("e1c1", divided)


class TestPerftIsSensitive(unittest.TestCase):
    """Le compte doit réagir à la position, sinon il ne prouve rien."""

    def test_a_different_position_gives_a_different_count(self):
        start = position("initiale")
        after_e4 = start.apply(
            next(m for m in start.legal_moves() if str(m) == "e2e4")
        )
        self.assertNotEqual(perft(after_e4, 2), perft(start, 2))

    def test_the_six_positions_do_not_agree_with_each_other(self):
        counts = {name: perft(position(name), 2) for name in REFERENCE}
        self.assertEqual(len(set(counts.values())), len(counts))


if __name__ == "__main__":
    unittest.main()

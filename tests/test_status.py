"""Le verdict d'une position : mat, pat, nulles de compteur et de matériel.

Ce que `is_it_checkmate` et `_is_pat` faisaient par raisonnement de cas devient
ici une conséquence : plus aucun coup légal, et l'échec tranche entre les deux.
"""

import unittest

from chess_engine.game_position import Status
from helpers import GamePosition, square

STARTPOS = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

#: Mat du couloir : la tour tient la huitième, les pions bouchent la fuite.
BACK_RANK_MATE = "R5k1/5ppp/8/8/8/8/8/6K1 b - - 4 40"

#: Roi noir en a8, dame blanche en b6 : aucune case libre, aucun échec.
STALEMATE = "k7/8/1Q6/8/8/8/8/7K b - - 4 40"


def status_of(fen):
    return GamePosition.from_fen(fen).status()


class TestGameOverByNoMove(unittest.TestCase):
    def test_checkmate(self):
        self.assertIs(status_of(BACK_RANK_MATE), Status.CHECKMATE)

    def test_stalemate(self):
        self.assertIs(status_of(STALEMATE), Status.STALEMATE)

    def test_the_start_is_ongoing(self):
        self.assertIs(status_of(STARTPOS), Status.ONGOING)

    def test_being_in_check_is_not_enough(self):
        """Échec simple, avec des réponses : la partie continue."""
        self.assertIs(status_of("4r3/8/8/8/8/8/8/4K2k w - - 0 1"), Status.ONGOING)


class TestTheFiftyMoveRule(unittest.TestCase):
    def test_a_hundred_plies_draw(self):
        self.assertIs(status_of("4k3/8/8/8/8/8/4R3/4K3 w - - 100 80"), Status.FIFTY_MOVE)

    def test_ninety_nine_do_not(self):
        self.assertIs(status_of("4k3/8/8/8/8/8/4R3/4K3 w - - 99 80"), Status.ONGOING)

    def test_mate_still_wins_over_the_clock(self):
        """Un mat reste un mat, même au centième demi-coup sans prise."""
        self.assertIs(
            status_of(BACK_RANK_MATE.replace(" 4 40", " 100 80")), Status.CHECKMATE
        )

    def test_stalemate_too(self):
        self.assertIs(
            status_of(STALEMATE.replace(" 4 40", " 100 80")), Status.STALEMATE
        )


class TestInsufficientMaterial(unittest.TestCase):
    def test_the_dead_positions(self):
        for name, fen in {
            "roi contre roi": "4k3/8/8/8/8/8/8/4K3 w - - 0 1",
            "roi et fou contre roi": "4k3/8/8/8/8/8/8/4KB2 w - - 0 1",
            "roi et cavalier contre roi": "4k3/8/8/8/8/8/8/4KN2 w - - 0 1",
            "fous de même couleur": "5b2/8/8/8/8/8/8/2B1K2k w - - 0 1",
        }.items():
            with self.subTest(position=name):
                self.assertIs(status_of(fen), Status.INSUFFICIENT_MATERIAL)

    def test_what_still_allows_a_mate(self):
        for name, fen in {
            "une tour": "4k3/8/8/8/8/8/8/4KR2 w - - 0 1",
            "une dame": "4k3/8/8/8/8/8/8/4KQ2 w - - 0 1",
            "un pion, qui peut promouvoir": "4k3/8/8/8/8/8/4P3/4K3 w - - 0 1",
            "deux cavaliers : possible, pas forçable": "4k3/8/8/8/8/8/8/3NKN2 w - - 0 1",
            "fous de couleurs opposées": "2b5/8/8/8/8/8/8/2B1K2k w - - 0 1",
            "un fou contre un cavalier": "2b5/8/8/8/8/8/8/3NK2k w - - 0 1",
        }.items():
            with self.subTest(position=name):
                self.assertIs(status_of(fen), Status.ONGOING)

    def test_it_is_read_from_the_pieces_not_the_move_count(self):
        bare = GamePosition.from_fen("4k3/8/8/8/8/8/8/4K3 w - - 0 1")
        self.assertTrue(bare.has_insufficient_material())
        self.assertTrue(bare.legal_moves())  # les rois bougent encore


class TestRepetitionKey(unittest.TestCase):
    def test_it_drops_the_two_counters(self):
        key = GamePosition.from_fen(STARTPOS).repetition_key()
        self.assertEqual(key, "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq -")

    def test_two_paths_to_one_position_share_a_key(self):
        position = GamePosition.from_fen(STARTPOS)
        detour = position
        for text in ["g1f3", "g8f6", "f3g1", "f6g8"]:
            detour = detour.apply(
                next(m for m in detour.legal_moves() if str(m) == text)
            )
        self.assertEqual(position.repetition_key(), detour.repetition_key())

    def test_lost_castling_rights_make_it_a_different_position(self):
        """Même disposition, droits différents : ce n'est pas la même position."""
        with_rights = GamePosition.from_fen("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
        without = GamePosition.from_fen("r3k2r/8/8/8/8/8/8/R3K2R w - - 0 1")
        self.assertNotEqual(with_rights.repetition_key(), without.repetition_key())

    def test_the_side_to_move_counts(self):
        white = GamePosition.from_fen(STARTPOS)
        black = GamePosition.from_fen(STARTPOS.replace(" w ", " b "))
        self.assertNotEqual(white.repetition_key(), black.repetition_key())


class TestTheEnPassantSquareInTheKey(unittest.TestCase):
    """La FIDE compare les positions par les coups qu'elles permettent.

    Une case d'en passant que personne ne peut prendre n'en change aucun : la
    retenir dans la clé ferait manquer des répétitions bien réelles.
    """

    def test_a_double_push_nobody_can_answer_leaves_no_trace(self):
        after_d4 = GamePosition.from_fen(
            "rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq d3 0 1"
        )
        self.assertFalse(after_d4.en_passant_is_available())
        self.assertTrue(after_d4.repetition_key().endswith(" -"))

    def test_a_double_push_a_pawn_can_answer_stays_in_the_key(self):
        with_taker = GamePosition.from_fen(
            "rnbqkbnr/ppp1pppp/8/8/3Pp3/8/PPP1PPPP/RNBQKBNR b KQkq d3 0 1"
        )
        self.assertTrue(with_taker.en_passant_is_available())
        self.assertTrue(with_taker.repetition_key().endswith(" d3"))

    def test_a_pinned_pawn_cannot_answer(self):
        """dxc6 e.p. viderait d5 et découvrirait le roi a5 sur la tour h5."""
        pinned = GamePosition.from_fen("8/8/8/K1pP3r/8/8/8/7k w - c6 0 1")
        self.assertFalse(pinned.en_passant_is_available())
        self.assertTrue(pinned.repetition_key().endswith(" -"))
        self.assertNotIn("d5c6", {str(m) for m in pinned.legal_moves()})

    def test_the_square_itself_is_untouched(self):
        """Seule la clé ignore la case : la position, elle, la garde."""
        after_d4 = GamePosition.from_fen(
            "rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq d3 0 1"
        )
        self.assertEqual(after_d4.en_passant_square, square("d3"))
        self.assertIn(" d3 ", after_d4.to_fen())


class TestStatusVocabulary(unittest.TestCase):
    def test_ongoing_is_the_only_one_that_is_not_over(self):
        self.assertFalse(Status.ONGOING.is_over())
        for status in Status:
            if status is not Status.ONGOING:
                self.assertTrue(status.is_over(), status)

    def test_checkmate_is_the_only_ending_that_is_not_a_draw(self):
        self.assertFalse(Status.CHECKMATE.is_draw())
        for status in (
            Status.STALEMATE,
            Status.FIFTY_MOVE,
            Status.REPETITION,
            Status.INSUFFICIENT_MATERIAL,
        ):
            self.assertTrue(status.is_draw(), status)

    def test_the_values_serialise_as_plain_strings(self):
        self.assertEqual(Status.CHECKMATE, "checkmate")
        self.assertEqual(f"{Status.STALEMATE.value}", "stalemate")


if __name__ == "__main__":
    unittest.main()

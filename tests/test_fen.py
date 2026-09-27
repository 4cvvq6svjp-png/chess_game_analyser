"""La FEN : lire et écrire une position.

C'est la notation qui rend une position transportable -- vers un test, vers
une API, vers Stockfish. Les tests d'aller-retour portent sur la *chaîne* et
non sur l'objet : deux positions identiques contiennent des instances de
pièces distinctes, et c'est la FEN qui sert d'identité, y compris pour la
future détection de répétition.
"""

import unittest

from chess_engine import InvalidFen
from helpers import GamePosition, position_with, square

STARTPOS = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

#: Position de test de référence, dite « Kiwipete » (Peter McKenzie), choisie
#: parce qu'elle autorise les quatre roques dès le premier coup -- ce que la
#: position initiale ne permet jamais avant le cinquième.
KIWIPETE = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq -"


def play(position, *moves_text):
    """Joue une suite de coups en notation longue, en les exigeant légaux."""
    for text in moves_text:
        move = next((m for m in position.legal_moves() if str(m) == text), None)
        assert move is not None, f"{text} n'est pas légal ici"
        position = position.apply(move)
    return position


def placement_and_rights(position):
    """Les quatre premiers champs : ce qui fera la clé de la répétition."""
    return " ".join(position.to_fen().split()[:4])


class TestExport(unittest.TestCase):
    def test_the_starting_position_writes_itself(self):
        self.assertEqual(GamePosition.from_fen(STARTPOS).to_fen(), STARTPOS)

    def test_an_empty_board_is_eight_eights(self):
        self.assertTrue(position_with({}).to_fen().startswith("8/8/8/8/8/8/8/8 "))

    def test_no_castling_rights_writes_a_dash(self):
        bare = GamePosition.from_fen("8/8/8/8/8/8/8/K6k w - - 0 1")
        self.assertIn(" - - ", bare.to_fen())

    def test_the_king_moving_gives_up_its_rights_in_the_fen(self):
        position = play(GamePosition.from_fen(STARTPOS), "e2e4", "e7e5", "e1e2")
        self.assertIn(" kq ", position.to_fen())

    def test_the_en_passant_square_is_written(self):
        after = play(GamePosition.from_fen(STARTPOS), "e2e4")
        self.assertEqual(after.en_passant_square, square("e3"))
        self.assertIn(" e3 ", after.to_fen())


class TestImport(unittest.TestCase):
    def test_reads_the_starting_position(self):
        position = GamePosition.from_fen(STARTPOS)
        self.assertEqual(position.side_to_move, "w")
        self.assertEqual(position.castling_rights, frozenset("KQkq"))
        self.assertIsNone(position.en_passant_square)
        self.assertEqual(position.piece_at(square("e1")).name, "king")
        self.assertEqual(position.piece_at(square("e1")).color, "w")
        self.assertEqual(position.piece_at(square("d8")).name, "queen")
        self.assertEqual(position.piece_at(square("d8")).color, "b")
        self.assertIsNone(position.piece_at(square("e4")))

    def test_the_two_counters_are_optional(self):
        """Beaucoup de positions publiées s'arrêtent après la case d'en passant."""
        position = GamePosition.from_fen(KIWIPETE)
        self.assertEqual(position.halfmove_clock, 0)
        self.assertEqual(position.fullmove_number, 1)

    def test_counters_are_read_when_present(self):
        position = GamePosition.from_fen(
            "8/8/8/8/8/8/8/K6k b - - 17 42"
        )
        self.assertEqual(position.side_to_move, "b")
        self.assertEqual(position.halfmove_clock, 17)
        self.assertEqual(position.fullmove_number, 42)

    def test_an_en_passant_square_is_read(self):
        position = GamePosition.from_fen(
            "rnbqkbnr/pppp1ppp/8/4p3/8/8/PPPPPPPP/RNBQKBNR w KQkq e6 0 2"
        )
        self.assertEqual(position.en_passant_square, square("e6"))


class TestRoundTrip(unittest.TestCase):
    def test_writing_then_reading_preserves_the_position(self):
        for fen in [
            STARTPOS,
            "8/8/8/8/8/8/8/K6k w - - 0 1",
            "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
            "rnbqkbnr/pppp1ppp/8/4p3/8/8/PPPPPPPP/RNBQKBNR w Kq e6 3 7",
        ]:
            with self.subTest(fen=fen):
                self.assertEqual(GamePosition.from_fen(fen).to_fen(), fen)

    def test_it_survives_a_played_game(self):
        position = GamePosition.from_fen(STARTPOS)
        for text in ["e2e4", "c7c5", "g1f3", "d7d6", "d2d4", "c5d4"]:
            position = play(position, text)
            self.assertEqual(
                GamePosition.from_fen(position.to_fen()).to_fen(), position.to_fen()
            )

    def test_the_same_position_yields_the_same_string(self):
        """Ce qui fera la clé de la répétition : deux chemins, une seule FEN."""
        direct = GamePosition.from_fen(STARTPOS)
        detour = play(direct, "g1f3", "g8f6", "f3g1", "f6g8")
        self.assertEqual(placement_and_rights(direct), placement_and_rights(detour))


class TestRejectsNonsense(unittest.TestCase):
    def test_too_few_fields(self):
        with self.assertRaises(InvalidFen):
            GamePosition.from_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w")

    def test_wrong_number_of_ranks(self):
        with self.assertRaises(InvalidFen):
            GamePosition.from_fen("8/8/8/8/8/8/8 w - - 0 1")

    def test_a_rank_that_does_not_add_up(self):
        with self.assertRaises(InvalidFen):
            GamePosition.from_fen("8/8/8/8/8/8/8/KKK w - - 0 1")

    def test_an_unknown_piece(self):
        with self.assertRaises(InvalidFen):
            GamePosition.from_fen("8/8/8/8/8/8/8/X7 w - - 0 1")

    def test_an_invalid_side_to_move(self):
        with self.assertRaises(InvalidFen):
            GamePosition.from_fen("8/8/8/8/8/8/8/K6k x - - 0 1")

    def test_invalid_castling_rights(self):
        with self.assertRaises(InvalidFen):
            GamePosition.from_fen("8/8/8/8/8/8/8/K6k w KQxq - 0 1")

    def test_an_impossible_en_passant_square(self):
        with self.assertRaises(InvalidFen):
            GamePosition.from_fen("8/8/8/8/8/8/8/K6k w - z9 0 1")


class TestFenFeedsTheGenerator(unittest.TestCase):
    def test_a_position_read_from_fen_can_be_played(self):
        position = GamePosition.from_fen(STARTPOS)
        self.assertEqual(len(position.legal_moves()), 20)

    def test_kiwipete_parses_and_generates(self):
        position = GamePosition.from_fen(KIWIPETE)
        self.assertEqual(position.side_to_move, "w")
        self.assertEqual(position.castling_rights, frozenset("KQkq"))
        self.assertEqual(len(position.legal_moves()), 48)


if __name__ == "__main__":
    unittest.main()

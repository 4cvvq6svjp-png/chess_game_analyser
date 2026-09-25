"""L'écriture du SAN : la notation que lit un joueur, et que le front affiche.

Chaque attendu a été vérifié contre ``python-chess``. Le corpus de parties
rejouées fait la même vérification à grande échelle (``test_replayed_games``) ;
ici, on isole les cas qu'une partie réelle ne garantit pas de traverser.
"""

import unittest

from chess_engine import Game, IllegalMove
from helpers import GamePosition

STARTPOS = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def san_of(fen, text):
    position = GamePosition.from_fen(fen)
    move = next(m for m in position.legal_moves() if str(m) == text)
    return position.san(move)


class TestPiecesAndPawns(unittest.TestCase):
    def test_a_piece_is_named_by_its_letter(self):
        self.assertEqual(san_of(STARTPOS, "g1f3"), "Nf3")

    def test_a_pawn_is_named_by_nothing(self):
        self.assertEqual(san_of(STARTPOS, "e2e4"), "e4")

    def test_a_pawn_capture_names_the_file_it_leaves(self):
        fen = "rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 2"
        self.assertEqual(san_of(fen, "e4d5"), "exd5")

    def test_en_passant_is_written_as_the_capture_it_is(self):
        """La case d'arrivée est vide : c'est le changement de colonne qui dit la prise."""
        fen = "rnbqkbnr/ppp1p1pp/8/3pPp2/8/8/PPPP1PPP/RNBQKBNR w KQkq f6 0 3"
        self.assertEqual(san_of(fen, "e5f6"), "exf6")

    def test_a_piece_capture_takes_an_x(self):
        fen = "4k3/8/8/3p4/8/2N5/8/4K3 w - - 0 1"
        self.assertEqual(san_of(fen, "c3d5"), "Nxd5")


class TestDisambiguation(unittest.TestCase):
    """La case de départ n'apparaît que si deux pièces semblables visent la même arrivée."""

    def test_by_file_first(self):
        self.assertEqual(san_of("4k3/8/8/8/8/8/8/1N2KN2 w - - 0 1", "b1d2"), "Nbd2")

    def test_by_rank_when_the_file_is_shared(self):
        self.assertEqual(san_of("4k3/8/8/R7/8/8/8/R3K3 w - - 0 1", "a1a3"), "R1a3")

    def test_by_both_when_neither_suffices(self):
        """Trois dames : h1 partage la colonne, e4 la rangée."""
        self.assertEqual(san_of("k7/8/8/8/4Q2Q/8/8/K6Q w - - 0 1", "h4e1"), "Qh4e1+")

    def test_a_pinned_rival_does_not_count(self):
        """Le cavalier f1 est cloué par la tour h1 : il ne va nulle part."""
        self.assertEqual(san_of("4k3/8/8/8/8/8/8/1N1K1N1r w - - 0 1", "b1d2"), "Nd2")


class TestSpecialMoves(unittest.TestCase):
    def test_castling_kingside(self):
        self.assertEqual(san_of("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1", "e1g1"), "O-O")

    def test_castling_queenside(self):
        self.assertEqual(san_of("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1", "e1c1"), "O-O-O")

    def test_a_castle_can_give_check(self):
        """C'est la tour qui donne l'échec : le suffixe se lit sur la position d'après."""
        self.assertEqual(san_of("5k2/8/8/8/8/8/8/4K2R w K - 0 1", "e1g1"), "O-O+")

    def test_promotion(self):
        self.assertEqual(san_of("8/4P3/8/8/8/8/8/k3K3 w - - 0 1", "e7e8n"), "e8=N")

    def test_promotion_with_capture_and_check(self):
        self.assertEqual(san_of("3r2k1/4P3/8/8/8/8/8/4K3 w - - 0 1", "e7d8q"), "exd8=Q+")


class TestCheckAndMate(unittest.TestCase):
    def test_mate_is_a_hash(self):
        fen = "rnbqkbnr/pppp1ppp/8/4p3/6P1/5P2/PPPPP2P/RNBQKBNR b KQkq g3 0 2"
        self.assertEqual(san_of(fen, "d8h4"), "Qh4#")

    def test_a_check_that_is_not_mate_is_a_plus(self):
        self.assertEqual(san_of("4k3/8/8/8/8/8/8/R3K3 w - - 0 1", "a1a8"), "Ra8+")


class TestRefusal(unittest.TestCase):
    def test_an_illegal_move_has_no_notation(self):
        position = GamePosition.from_fen(STARTPOS)
        illegal = GamePosition.from_fen("4k3/8/8/8/8/8/8/R3K3 w - - 0 1").legal_moves()[0]
        with self.assertRaises(IllegalMove):
            position.san(illegal)


class TestTheGameKeepsItsNotation(unittest.TestCase):
    def test_parallel_to_the_moves(self):
        game = Game()
        for text in ["e2e4", "e7e5", "g1f3", "b8c6", "f1b5"]:
            game.play_text(text)
        self.assertEqual(game.san(), ["e4", "e5", "Nf3", "Nc6", "Bb5"])

    def test_follows_the_game_as_it_grows(self):
        game = Game()
        game.play_text("e2e4")
        self.assertEqual(game.san(), ["e4"])
        game.play_text("e7e5")
        self.assertEqual(game.san(), ["e4", "e5"])

    def test_catches_up_with_moves_added_behind_its_back(self):
        """``moves`` est une liste publique : ce qu'on y ajoute sans ``play`` compte aussi."""
        game = Game()
        game.play_text("e2e4")
        game.moves.append(game.current_position.legal_moves()[0])
        self.assertEqual(len(game.san()), 2)
        self.assertEqual(game.san()[0], "e4")

    def test_an_empty_game_has_no_notation(self):
        self.assertEqual(Game().san(), [])

    def test_starts_from_the_game_s_own_position(self):
        game = Game(initial_fen="r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1")
        game.play_text("e8c8")
        self.assertEqual(game.san(), ["O-O-O"])


if __name__ == "__main__":
    unittest.main()

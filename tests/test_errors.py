"""Les refus typés : ce sur quoi l'API choisira entre 409 et 422.

Les tests de règles vérifient *qu'un* refus a lieu ; ceux-ci vérifient qu'il
porte le bon type et les bons attributs, parce que c'est le contrat que la
couche web lira (``docs/api-contract.md``, §2 et §7).
"""

import unittest

from chess_engine import (
    ChessError,
    Game,
    GameOver,
    GamePosition,
    IllegalMove,
    InvalidFen,
    Move,
    Status,
    UnknownColor,
)

FOOLS_MATE = ["f2f3", "e7e5", "g2g4", "d8h4"]


def game_after(*moves_text):
    game = Game()
    for text in moves_text:
        game.play_text(text)
    return game


class TestTheHierarchy(unittest.TestCase):
    def test_every_refusal_is_a_chess_error(self):
        for error_type in (IllegalMove, GameOver, UnknownColor, InvalidFen):
            with self.subTest(error=error_type.__name__):
                self.assertTrue(issubclass(error_type, ChessError))

    def test_and_still_a_value_error(self):
        """Ce qui attrapait ``ValueError`` -- le terminal -- continue de marcher."""
        self.assertTrue(issubclass(ChessError, ValueError))


class TestIllegalMove(unittest.TestCase):
    def test_carries_the_move_as_written(self):
        with self.assertRaises(IllegalMove) as caught:
            game_after("e2e5")
        self.assertEqual(caught.exception.move, "e2e5")

    def test_nonsense_is_an_illegal_move_too(self):
        with self.assertRaises(IllegalMove) as caught:
            game_after("pouet")
        self.assertEqual(caught.exception.move, "pouet")

    def test_through_play_as_well_as_play_text(self):
        game = Game()
        with self.assertRaises(IllegalMove) as caught:
            game.play(Move((6, 4), (3, 4)))  # e2e5
        self.assertEqual(caught.exception.move, "e2e5")


class TestGameOver(unittest.TestCase):
    def test_carries_the_status(self):
        game = game_after(*FOOLS_MATE)
        with self.assertRaises(GameOver) as caught:
            game.play_text("e1e2")
        self.assertIs(caught.exception.status, Status.CHECKMATE)

    def test_wins_over_illegal_move(self):
        """Après un mat, aucun coup n'est légal ; la raison à donner reste la fin de partie.

        Chercher le coup d'abord répondait « illégal ». Le client, lui, doit
        savoir que la partie est finie, pas qu'il a mal joué.
        """
        game = game_after(*FOOLS_MATE)
        for text in ["a2a3", "pouet"]:
            with self.subTest(move=text):
                with self.assertRaises(GameOver):
                    game.play_text(text)

    def test_after_a_resignation(self):
        game = game_after("e2e4")
        game.resign("b")
        with self.assertRaises(GameOver) as caught:
            game.play_text("g1f3")
        self.assertIs(caught.exception.status, Status.RESIGNATION)

    def test_resigning_a_finished_game(self):
        game = game_after(*FOOLS_MATE)
        with self.assertRaises(GameOver) as caught:
            game.resign("w")
        self.assertIs(caught.exception.status, Status.CHECKMATE)


class TestUnknownColor(unittest.TestCase):
    def test_carries_the_color(self):
        with self.assertRaises(UnknownColor) as caught:
            Game().resign("white")
        self.assertEqual(caught.exception.color, "white")

    def test_is_checked_before_the_game_being_over(self):
        """Une requête mal formée l'est quel que soit l'état de la partie."""
        game = game_after(*FOOLS_MATE)
        with self.assertRaises(UnknownColor):
            game.resign("white")


class TestInvalidFen(unittest.TestCase):
    def test_carries_the_fen_and_the_reason(self):
        with self.assertRaises(InvalidFen) as caught:
            GamePosition.from_fen("8/8/8 w - -")
        self.assertEqual(caught.exception.fen, "8/8/8 w - -")
        self.assertIn("8 rangées", caught.exception.reason)

    def test_covers_what_fails_below_the_parser(self):
        """Un compteur illisible, une case hors échiquier : c'est toujours la FEN."""
        for fen in [
            "4k3/8/8/8/8/8/8/4K3 w - - x 1",
            "4k3/8/8/8/8/8/8/4K3 w - z9 0 1",
        ]:
            with self.subTest(fen=fen):
                with self.assertRaises(InvalidFen):
                    GamePosition.from_fen(fen)

    def test_a_game_cannot_start_from_one(self):
        with self.assertRaises(InvalidFen):
            Game(initial_fen="pas une fen")


if __name__ == "__main__":
    unittest.main()

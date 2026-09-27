"""Le format de transport : la forme durable d'une partie, et le document servi.

Deux formes, deux usages. ``Game.to_dict`` est ce qu'on stocke : le strict
nécessaire, dont tout le reste se déduit. ``game_document`` est ce que le
client reçoit : tout ce qu'il ne peut pas calculer lui-même, puisqu'il n'a
pas de moteur (``docs/api-contract.md``, §5).
"""

import json
import unittest

from chess_engine import ChessError, Game, GameOver, IllegalMove, InvalidFen, Status, game_document

FOOLS_MATE = ["f2f3", "e7e5", "g2g4", "d8h4"]
SHUFFLE = ["g1f3", "g8f6", "f3g1", "f6g8"]


def game_after(*moves_text, **options):
    game = Game(**options)
    for text in moves_text:
        game.play_text(text)
    return game


class TestTheStoredForm(unittest.TestCase):
    def test_holds_only_what_cannot_be_derived(self):
        stored = game_after("e2e4", "e7e5").to_dict()
        self.assertEqual(
            stored,
            {
                "initial_fen": Game().initial_fen,
                "moves": ["e2e4", "e7e5"],
                "auto_draw": True,
                "termination": None,
            },
        )

    def test_survives_json(self):
        game = game_after("e2e4", "e7e5")
        game.resign("b", at=1727000000.0)
        stored = game.to_dict()
        self.assertEqual(json.loads(json.dumps(stored)), stored)

    def test_a_game_comes_back_identical(self):
        game = game_after("e2e4", "c7c5", "g1f3", auto_draw=False)
        copy = Game.from_dict(game.to_dict())
        self.assertEqual(copy.to_dict(), game.to_dict())
        self.assertEqual(copy.current_position.to_fen(), game.current_position.to_fen())
        self.assertFalse(copy.auto_draw)

    def test_a_game_from_a_custom_position_comes_back(self):
        fen = "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"
        game = game_after("e1g1", initial_fen=fen)
        copy = Game.from_dict(game.to_dict())
        self.assertEqual(copy.initial_fen, fen)
        self.assertEqual(copy.current_position.to_fen(), game.current_position.to_fen())

    def test_a_resignation_comes_back_with_its_instant(self):
        game = game_after("e2e4")
        game.resign("w", at=1727000000.5)
        copy = Game.from_dict(game.to_dict())
        self.assertIs(copy.status(), Status.RESIGNATION)
        self.assertEqual(copy.termination, game.termination)
        self.assertEqual(copy.result(), "0-1")

    def test_the_repetition_count_comes_back(self):
        """Rejouer reconstruit aussi l'historique, que la répétition lit."""
        game = game_after(*SHUFFLE, *SHUFFLE)
        self.assertIs(Game.from_dict(game.to_dict()).status(), Status.REPETITION)


class TestAStoredGameIsRevalidated(unittest.TestCase):
    """Rejouer plutôt que recopier : une donnée corrompue ne passe pas."""

    def test_an_illegal_move_is_refused(self):
        stored = game_after("e2e4").to_dict()
        stored["moves"].append("e2e4")  # plus de pion en e2
        with self.assertRaises(IllegalMove):
            Game.from_dict(stored)

    def test_a_move_after_mate_is_refused(self):
        stored = game_after(*FOOLS_MATE).to_dict()
        stored["moves"].append("a2a3")
        with self.assertRaises(GameOver):
            Game.from_dict(stored)

    def test_a_bad_fen_is_refused(self):
        with self.assertRaises(InvalidFen):
            Game.from_dict({"initial_fen": "pas une fen", "moves": []})

    def test_an_ending_the_board_decides_cannot_be_recorded(self):
        """Un mat enregistré à la main contredirait l'échiquier."""
        stored = game_after("e2e4").to_dict()
        stored["termination"] = {"status": "checkmate", "by": "w", "at": 0.0}
        with self.assertRaises(ChessError):
            Game.from_dict(stored)

    def test_an_unknown_status_is_refused(self):
        stored = game_after("e2e4").to_dict()
        stored["termination"] = {"status": "boredom", "by": "w", "at": 0.0}
        with self.assertRaises(ChessError):
            Game.from_dict(stored)


class TestTheDocument(unittest.TestCase):
    def test_a_new_game(self):
        document = game_document(Game())
        self.assertEqual(document["ply"], 0)
        self.assertEqual(document["status"], "ongoing")
        self.assertIsNone(document["result"])
        self.assertEqual(document["side_to_move"], "w")
        self.assertFalse(document["in_check"])
        self.assertEqual(len(document["legal_moves"]), 20)
        self.assertEqual(document["moves"], [])
        self.assertEqual(document["san"], [])
        self.assertEqual(document["positions"], [Game().initial_fen])
        self.assertIsNone(document["termination"])

    def test_after_a_few_moves(self):
        document = game_document(game_after("e2e4", "e7e5", "g1f3"))
        self.assertEqual(document["ply"], 3)
        self.assertEqual(document["moves"], ["e2e4", "e7e5", "g1f3"])
        self.assertEqual(document["san"], ["e4", "e5", "Nf3"])
        self.assertEqual(
            document["fen"],
            "rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2",
        )
        self.assertEqual(document["side_to_move"], "b")
        self.assertIn("b8c6", document["legal_moves"])

    def test_one_position_per_ply_for_the_rewind(self):
        """``positions[i]`` est la position après ``i`` demi-coups : le client rembobine seul."""
        game = game_after("e2e4", "e7e5", "g1f3")
        document = game_document(game)
        self.assertEqual(len(document["positions"]), 4)
        self.assertEqual(document["positions"][0], game.initial_fen)
        self.assertEqual(document["positions"][-1], document["fen"])
        self.assertEqual(document["positions"][1], game.position_at(1).to_fen())

    def test_check_is_served(self):
        document = game_document(game_after("e2e4", "f7f6", "d1h5"))
        self.assertTrue(document["in_check"])
        self.assertEqual(document["san"][-1], "Qh5+")

    def test_a_mate(self):
        document = game_document(game_after(*FOOLS_MATE))
        self.assertEqual(document["status"], "checkmate")
        self.assertEqual(document["result"], "0-1")
        self.assertTrue(document["in_check"])
        self.assertEqual(document["legal_moves"], [])
        self.assertEqual(document["san"][-1], "Qh4#")

    def test_a_resigned_game_offers_no_move(self):
        """La position en permet vingt, mais la partie n'en accepte plus aucun."""
        game = Game()
        game.resign("w", at=1727000000.0)
        document = game_document(game)
        self.assertEqual(document["status"], "resignation")
        self.assertEqual(document["result"], "0-1")
        self.assertEqual(document["legal_moves"], [])
        self.assertEqual(
            document["termination"],
            {"status": "resignation", "by": "w", "at": 1727000000.0},
        )

    def test_a_draw_that_is_not_enforced_stays_playable(self):
        """Avec ``auto_draw=False`` la nulle est constatée, et la partie continue."""
        document = game_document(game_after(*SHUFFLE, *SHUFFLE, auto_draw=False))
        self.assertEqual(document["status"], "repetition")
        self.assertEqual(document["result"], "1/2-1/2")
        self.assertEqual(len(document["legal_moves"]), 20)

    def test_is_json_as_is(self):
        game = game_after(*FOOLS_MATE)
        document = game_document(game)
        self.assertEqual(json.loads(json.dumps(document)), document)


if __name__ == "__main__":
    unittest.main()

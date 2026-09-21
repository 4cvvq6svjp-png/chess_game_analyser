"""L'interface terminal.

Les entrées et sorties étant injectables, une partie entière se joue dans un
test : on fournit la liste des réponses, on lit ce qui a été écrit.
"""

import unittest

from chess_engine import GamePosition, Status
from chess_engine.cli import TerminalGame, parse_squares, render
from chess_engine.game_position import STARTING_FEN


class Script:
    """Un terminal en papier : des réponses préparées, et tout ce qui s'écrit."""

    def __init__(self, *answers):
        self.answers = list(answers)
        self.written = []

    def read(self, prompt=""):
        if not self.answers:
            raise EOFError
        return self.answers.pop(0)

    def write(self, text=""):
        self.written.append(str(text))

    @property
    def text(self):
        return "\n".join(self.written)


def run(*answers, fen=STARTING_FEN):
    script = Script(*answers)
    game = TerminalGame(initial_fen=fen, read=script.read, write=script.write)
    status = game.run()
    return script, game, status


class TestRender(unittest.TestCase):
    def test_the_starting_position(self):
        text = render(GamePosition.from_fen(STARTING_FEN))
        lines = text.splitlines()
        self.assertEqual(lines[0], "8 | r n b q k b n r |")
        self.assertEqual(lines[7], "1 | R N B Q K B N R |")
        self.assertEqual(lines[8], "    a b c d e f g h")

    def test_empty_squares_are_dots(self):
        text = render(GamePosition.from_fen("4k3/8/8/8/8/8/8/4K3 w - - 0 1"))
        self.assertEqual(text.splitlines()[1], "7 | . . . . . . . . |")

    def test_white_is_uppercase_and_black_lowercase(self):
        text = render(GamePosition.from_fen("4k3/8/8/8/8/8/8/4K3 w - - 0 1"))
        self.assertIn("k", text.splitlines()[0])
        self.assertIn("K", text.splitlines()[7])

    def test_the_knight_is_not_confused_with_the_king(self):
        text = render(GamePosition.from_fen(STARTING_FEN))
        self.assertEqual(text.splitlines()[7].count("N"), 2)
        self.assertEqual(text.splitlines()[7].count("K"), 1)


class TestParseSquares(unittest.TestCase):
    def test_reads_two_squares(self):
        self.assertEqual(parse_squares("e2/e4"), ((6, 4), (4, 4)))
        self.assertEqual(parse_squares("a1/a3"), ((7, 0), (5, 0)))

    def test_is_forgiving_about_case_and_spaces(self):
        self.assertEqual(parse_squares("  E2/E4 "), ((6, 4), (4, 4)))

    def test_refuses_what_is_not_two_squares(self):
        for text in ["e2e4", "e2/e4/e5", "", "pouet"]:
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_squares(text)

    def test_refuses_squares_off_the_board(self):
        for text in ["z1/a3", "e9/e4", "e2/e0"]:
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_squares(text)


class TestPlayingAGame(unittest.TestCase):
    def test_fools_mate_is_announced(self):
        script, game, status = run("f2/f3", "e7/e5", "g2/g4", "d8/h4")
        self.assertIs(status, Status.CHECKMATE)
        self.assertIn("Checkmate -- Black wins", script.text)
        self.assertIn("[0-1]", script.text)
        self.assertEqual(game.game.ply, 4)

    def test_an_unplayable_move_is_refused_and_the_game_goes_on(self):
        script, game, _ = run("e2/e5", "e2/e4")
        self.assertIn("Ce coup n'est pas jouable", script.text)
        self.assertEqual(game.game.ply, 1)

    def test_malformed_input_is_refused_and_the_game_goes_on(self):
        script, game, _ = run("pouet", "e2/e4")
        self.assertIn("case/case", script.text)
        self.assertEqual(game.game.ply, 1)

    def test_running_out_of_input_stops_cleanly(self):
        script, game, status = run("e2/e4")
        self.assertIs(status, Status.ONGOING)
        self.assertIn("Partie interrompue", script.text)

    def test_check_is_announced(self):
        script, _, _ = run(fen="4r3/8/8/8/8/8/8/4K2k w - - 0 1")
        self.assertIn("CHECK!", script.text)

    def test_the_castle_moves_the_rook(self):
        _, game, _ = run("e1/g1", fen="r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1")
        board = game.game.current_position
        self.assertEqual(board.piece_at((7, 6)).name, "king")
        self.assertEqual(board.piece_at((7, 5)).name, "rook")


class TestPromotion(unittest.TestCase):
    PROMOTING = "4k3/P7/8/8/8/8/8/4K3 w - - 0 1"

    def test_the_player_is_asked_which_piece(self):
        script, game, _ = run("a7/a8", "queen", fen=self.PROMOTING)
        promoted = game.game.current_position.piece_at((0, 0))
        self.assertEqual(promoted.name, "queen")
        self.assertEqual(promoted.color, "w")

    def test_another_piece_can_be_chosen(self):
        _, game, _ = run("a7/a8", "knight", fen=self.PROMOTING)
        self.assertEqual(game.game.current_position.piece_at((0, 0)).name, "knight")

    def test_an_unknown_piece_is_refused(self):
        script, game, _ = run("a7/a8", "dragon", fen=self.PROMOTING)
        self.assertIn("Pièce inconnue", script.text)
        self.assertEqual(game.game.ply, 0)

    def test_a_plain_move_asks_nothing(self):
        """Un seul coup possible pour ce déplacement : pas de question."""
        script, game, _ = run("e1/e2", fen=self.PROMOTING)
        self.assertNotIn("Promotion", script.text)
        self.assertEqual(game.game.ply, 1)


if __name__ == "__main__":
    unittest.main()

"""La partie : l'historique, le rembobinage et la triple répétition.

Une partie ne stocke pas ses positions, elle les déduit de sa liste de coups.
C'est ce qui rend le rembobinage gratuit -- et ce qui permet de compter les
répétitions, la seule règle qu'aucune position ne peut trancher seule.
"""

import time
import unittest

from chess_engine import Game, GameOver, GamePosition, IllegalMove, Status, UnknownColor

FOOLS_MATE = ["f2f3", "e7e5", "g2g4", "d8h4"]
SCHOLARS_MATE = ["e2e4", "e7e5", "f1c4", "b8c6", "d1h5", "g8f6", "h5f7"]
SHUFFLE = ["g1f3", "g8f6", "f3g1", "f6g8"]


def game_after(*moves_text, fen=None):
    game = Game(initial_fen=fen) if fen else Game()
    for text in moves_text:
        game.play_text(text)
    return game


class TestANewGame(unittest.TestCase):
    def test_starts_at_the_initial_position(self):
        game = Game()
        self.assertEqual(game.ply, 0)
        self.assertEqual(game.current_position.to_fen(), game.initial_fen)
        self.assertIs(game.status(), Status.ONGOING)
        self.assertIsNone(game.result())

    def test_can_start_from_any_position(self):
        game = Game(initial_fen="4k3/8/8/8/8/8/4P3/4K3 w - - 0 1")
        # le roi a quatre cases (e2 est tenue par son pion), le pion en a deux
        self.assertEqual(len(game.current_position.legal_moves()), 6)
        self.assertIs(game.status(), Status.ONGOING)

    def test_a_move_advances_it(self):
        game = game_after("e2e4")
        self.assertEqual(game.ply, 1)
        self.assertEqual(game.current_position.side_to_move, "b")


class TestRefusingMoves(unittest.TestCase):
    def test_an_illegal_move_is_refused(self):
        with self.assertRaises(IllegalMove):
            game_after("e2e5")

    def test_nonsense_is_refused(self):
        with self.assertRaises(IllegalMove):
            game_after("pouet")

    def test_nothing_can_be_played_after_a_mate(self):
        game = game_after(*FOOLS_MATE)
        with self.assertRaises(GameOver):
            game.play_text("e1e2")

    def test_a_refused_move_leaves_the_history_untouched(self):
        game = game_after("e2e4")
        with self.assertRaises(IllegalMove):
            game.play_text("e4e6")
        self.assertEqual(game.ply, 1)


class TestRewind(unittest.TestCase):
    def test_ply_zero_is_the_start(self):
        game = game_after(*SCHOLARS_MATE)
        self.assertEqual(game.position_at(0).to_fen(), game.initial_fen)

    def test_every_ply_is_reachable(self):
        game = game_after(*SCHOLARS_MATE)
        self.assertEqual(len(game.positions()), len(SCHOLARS_MATE) + 1)
        self.assertEqual(
            game.position_at(game.ply).to_fen(), game.current_position.to_fen()
        )

    def test_looking_back_changes_nothing(self):
        game = game_after(*SCHOLARS_MATE)
        before = game.current_position.to_fen()
        game.position_at(2)
        game.position_at(0)
        self.assertEqual(game.current_position.to_fen(), before)
        self.assertEqual(game.ply, len(SCHOLARS_MATE))

    def test_a_ply_beyond_the_game_is_refused(self):
        game = game_after("e2e4")
        with self.assertRaises(IndexError):
            game.position_at(5)

    def test_the_history_replays_identically(self):
        """Une partie reconstruite depuis ses coups est la même partie."""
        played = game_after(*SCHOLARS_MATE)
        rebuilt = Game(moves=list(played.moves))
        self.assertEqual(
            rebuilt.current_position.to_fen(), played.current_position.to_fen()
        )
        self.assertIs(rebuilt.status(), played.status())


class TestCheckmateResults(unittest.TestCase):
    def test_fools_mate_is_won_by_black(self):
        game = game_after(*FOOLS_MATE)
        self.assertIs(game.status(), Status.CHECKMATE)
        self.assertEqual(game.result(), "0-1")

    def test_scholars_mate_is_won_by_white(self):
        game = game_after(*SCHOLARS_MATE)
        self.assertIs(game.status(), Status.CHECKMATE)
        self.assertEqual(game.result(), "1-0")

    def test_an_unfinished_game_has_no_result(self):
        self.assertIsNone(game_after("e2e4", "e7e5").result())


class TestThreefoldRepetition(unittest.TestCase):
    def test_two_visits_are_not_enough(self):
        game = game_after(*SHUFFLE)
        self.assertEqual(game.repetition_count(), 2)
        self.assertIs(game.status(), Status.ONGOING)

    def test_the_third_visit_draws(self):
        game = game_after(*SHUFFLE, *SHUFFLE)
        self.assertEqual(game.repetition_count(), 3)
        self.assertIs(game.status(), Status.REPETITION)
        self.assertEqual(game.result(), "1/2-1/2")

    def test_it_counts_positions_and_not_moves(self):
        """Les huit coups sont tous différents ; c'est la position qui revient."""
        game = game_after(*SHUFFLE, *SHUFFLE)
        self.assertEqual(len(game.moves), 8)
        self.assertEqual(len({str(m) for m in game.moves}), 4)

    def test_the_count_follows_the_current_position_only(self):
        """Repartir d'ailleurs remet le compteur à une seule occurrence."""
        game = game_after(*SHUFFLE)
        self.assertEqual(game.repetition_count(), 2)
        game.play_text("e2e4")
        self.assertEqual(game.repetition_count(), 1)
        self.assertIs(game.status(), Status.ONGOING)


class TestDrawsByCounter(unittest.TestCase):
    def test_the_fifty_move_rule_is_reported(self):
        game = Game(initial_fen="4k3/8/8/8/8/8/4R3/4K3 w - - 100 80")
        self.assertIs(game.status(), Status.FIFTY_MOVE)
        self.assertEqual(game.result(), "1/2-1/2")

    def test_and_it_stops_the_game(self):
        """Choix assumé : la nulle est immédiate, pas une réclamation."""
        game = Game(initial_fen="4k3/8/8/8/8/8/4R3/4K3 w - - 100 80")
        with self.assertRaises(GameOver):
            game.play_text("e2e3")
        self.assertEqual(game.ply, 0)

    def test_a_repetition_stops_it_too(self):
        game = game_after(*SHUFFLE, *SHUFFLE)
        self.assertIs(game.status(), Status.REPETITION)
        with self.assertRaises(GameOver):
            game.play_text("e2e4")

    def test_insufficient_material_stops_it_too(self):
        game = Game(initial_fen="4k3/8/8/8/8/8/8/4KB2 w - - 0 1")
        with self.assertRaises(GameOver):
            game.play_text("e1e2")

    def test_insufficient_material_ends_it(self):
        game = Game(initial_fen="4k3/8/8/8/8/8/8/4KB2 w - - 0 1")
        self.assertIs(game.status(), Status.INSUFFICIENT_MATERIAL)
        self.assertEqual(game.result(), "1/2-1/2")


class TestClaimableDraws(unittest.TestCase):
    """``auto_draw=False`` : status() dit toujours la vérité, play() n'y cède plus.

    C'est ce qu'il faut pour rejouer une partie d'archive : les joueurs d'une
    répétition triple non réclamée ont continué, et le moteur doit les suivre.
    """

    def test_a_repetition_can_be_played_through(self):
        game = Game(auto_draw=False)
        for text in (*SHUFFLE, *SHUFFLE):
            game.play_text(text)
        self.assertIs(game.status(), Status.REPETITION)
        game.play_text("e2e4")
        self.assertEqual(game.ply, 9)

    def test_the_fifty_move_rule_can_be_played_through(self):
        game = Game(initial_fen="4k3/8/8/8/8/8/4R3/4K3 w - - 100 80", auto_draw=False)
        self.assertIs(game.status(), Status.FIFTY_MOVE)
        game.play_text("e2e3")
        self.assertEqual(game.ply, 1)

    def test_a_mate_still_stops_everything(self):
        """Une fin par absence de coup ne se réclame pas : elle s'impose."""
        game = Game(auto_draw=False)
        for text in FOOLS_MATE:
            game.play_text(text)
        self.assertIs(game.status(), Status.CHECKMATE)
        with self.assertRaises(GameOver):
            game.play_text("e1e2")

    def test_the_default_is_still_to_stop(self):
        self.assertTrue(Game().auto_draw)


class TestResignation(unittest.TestCase):
    """Une fin décidée par un joueur, enregistrée et non déduite."""

    def test_it_takes_effect_without_anyone_trying_a_move(self):
        """Le point de la chose : la lecture suivante suffit à la voir."""
        game = game_after("e2e4", "e7e5")
        self.assertIs(game.status(), Status.ONGOING)

        returned = game.resign("w")

        self.assertIs(returned, Status.RESIGNATION)
        self.assertIs(game.status(), Status.RESIGNATION)
        self.assertTrue(game.is_over())

    def test_the_position_alone_would_still_say_ongoing(self):
        """La fin est sur la partie, pas sur l'échiquier."""
        game = game_after("e2e4", "e7e5")
        game.resign("b")
        self.assertIs(game.current_position.status(), Status.ONGOING)
        self.assertIs(game.status(), Status.RESIGNATION)

    def test_the_side_that_resigns_is_the_side_that_loses(self):
        white_quits = game_after("e2e4", "e7e5")
        white_quits.resign("w")
        self.assertEqual(white_quits.result(), "0-1")

        black_quits = game_after("e2e4", "e7e5")
        black_quits.resign("b")
        self.assertEqual(black_quits.result(), "1-0")

    def test_it_does_not_depend_on_whose_turn_it_is(self):
        """Abandonner pendant le tour adverse reste possible, et perd."""
        game = game_after("e2e4")  # au trait : les noirs
        game.resign("w")
        self.assertEqual(game.current_position.side_to_move, "b")
        self.assertEqual(game.result(), "0-1")

    def test_nothing_can_be_played_afterwards(self):
        game = game_after("e2e4", "e7e5")
        game.resign("w")
        with self.assertRaises(GameOver):
            game.play_text("g1f3")
        self.assertEqual(game.ply, 2)

    def test_the_moves_already_played_are_kept(self):
        game = game_after(*SCHOLARS_MATE[:4])
        game.resign("b")
        self.assertEqual(game.ply, 4)
        self.assertEqual(len(game.positions()), 5)
        self.assertEqual(game.position_at(0).to_fen(), game.initial_fen)

    def test_the_instant_is_recorded_and_can_be_supplied(self):
        """C'est lui qui figera l'horloge : il ne doit pas être reconstitué."""
        game = game_after("e2e4")
        game.resign("w", at=1700000000.0)
        self.assertEqual(game.termination.at, 1700000000.0)
        self.assertEqual(game.termination.by, "w")
        self.assertIs(game.termination.status, Status.RESIGNATION)

    def test_the_instant_defaults_to_now(self):
        before = time.time()
        game = game_after("e2e4")
        game.resign("b")
        self.assertGreaterEqual(game.termination.at, before)
        self.assertLessEqual(game.termination.at, time.time())

    def test_the_record_is_frozen(self):
        game = game_after("e2e4")
        game.resign("w")
        with self.assertRaises(Exception):
            game.termination.by = "b"

    def test_resigning_twice_is_refused(self):
        game = game_after("e2e4")
        game.resign("w")
        with self.assertRaises(GameOver):
            game.resign("b")
        self.assertEqual(game.termination.by, "w")

    def test_a_finished_game_cannot_be_resigned(self):
        game = game_after(*FOOLS_MATE)
        with self.assertRaises(GameOver):
            game.resign("w")
        self.assertIs(game.status(), Status.CHECKMATE)

    def test_an_unknown_colour_is_refused(self):
        game = game_after("e2e4")
        for colour in ["white", "W", "", None]:
            with self.subTest(colour=colour):
                with self.assertRaises(UnknownColor):
                    game.resign(colour)
        self.assertIsNone(game.termination)

    def test_a_resignation_is_not_a_draw(self):
        self.assertFalse(Status.RESIGNATION.is_draw())
        self.assertTrue(Status.RESIGNATION.is_over())

    def test_it_still_works_on_a_game_reported_drawn_but_playable(self):
        """auto_draw=False : la partie continue, donc on peut encore abandonner."""
        game = Game(auto_draw=False)
        for text in (*SHUFFLE, *SHUFFLE):
            game.play_text(text)
        self.assertIs(game.status(), Status.REPETITION)
        self.assertFalse(game.is_over())

        game.resign("b")
        self.assertIs(game.status(), Status.RESIGNATION)
        self.assertEqual(game.result(), "1-0")
        self.assertTrue(game.is_over())


class TestTheHistoryIsTheSource(unittest.TestCase):
    def test_positions_follow_a_move_appended_by_hand(self):
        game = game_after("e2e4")
        move = next(
            m for m in game.current_position.legal_moves() if str(m) == "e7e5"
        )
        game.moves.append(move)
        self.assertEqual(game.ply, 2)
        self.assertEqual(len(game.positions()), 3)
        self.assertEqual(
            game.current_position.to_fen(),
            GamePosition.from_fen(game.initial_fen)
            .apply(game.moves[0])
            .apply(game.moves[1])
            .to_fen(),
        )


if __name__ == "__main__":
    unittest.main()

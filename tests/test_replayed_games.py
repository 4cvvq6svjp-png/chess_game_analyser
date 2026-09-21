"""Des parties réelles, rejouées coup par coup.

Ce que perft ne peut pas voir : il compte des nœuds, il ne passe jamais par
l'historique, ne demande jamais « était-ce un mat ? » et ne vérifie jamais
qu'une suite de centaines de coups retombe sur la bonne position. Ici on
rejoue des parties de Morphy et d'Alekhine et on exige la FEN finale exacte.

Le corpus est figé dans ``data/replayed_games.json`` : aucun accès réseau au
moment des tests. Il a été produit par ``tools/build_game_corpus.py``, qui
utilise ``python-chess`` comme oracle -- convertir les parties avec notre
propre moteur aurait été circulaire.

Les parties sont rejouées avec ``auto_draw=False``. Une partie d'archive a pu
franchir une triple répétition sans que personne ne réclame la nulle, et c'est
précisément le cas qu'on veut suivre jusqu'au bout.
"""

import json
import pathlib
import unittest

from helpers import Game, Status

CORPUS = json.loads(
    (pathlib.Path(__file__).parent / "data/replayed_games.json").read_text("utf-8")
)
GAMES = CORPUS["games"]

STATUS_BY_NAME = {
    "checkmate": Status.CHECKMATE,
    "stalemate": Status.STALEMATE,
    "ongoing": Status.ONGOING,
}


def replay(game_data):
    """Rejoue une partie, en signalant précisément où elle achoppe."""
    game = Game(auto_draw=False)
    for index, text in enumerate(game_data["moves"], start=1):
        try:
            game.play_text(text)
        except ValueError as error:
            raise AssertionError(
                f"{game_data['id']} : demi-coup {index} ({text}) refusé -- {error}\n"
                f"  position : {game.current_position.to_fen()}"
            ) from error
    return game


class TestTheCorpusItself(unittest.TestCase):
    """Un corpus vide ou tronqué passerait tous les autres tests en silence."""

    def test_it_holds_several_games(self):
        self.assertGreaterEqual(len(GAMES), 5)

    def test_every_game_has_what_it_takes(self):
        for game_data in GAMES:
            with self.subTest(game=game_data["id"]):
                self.assertGreater(len(game_data["moves"]), 10)
                self.assertTrue(game_data["final_fen"])
                self.assertIn(game_data["final_status"], STATUS_BY_NAME)

    def test_the_rare_rules_are_covered(self):
        covered = {rule for game in GAMES for rule in game["covers"]}
        for rule in [
            "O-O",
            "O-O-O",
            "en_passant",
            "promotion",
            "underpromotion",
            "checkmate",
            "repetition_played_through",
        ]:
            with self.subTest(rule=rule):
                self.assertIn(rule, covered)


class TestReplay(unittest.TestCase):
    def test_every_move_of_every_game_is_legal(self):
        for game_data in GAMES:
            with self.subTest(game=game_data["id"]):
                game = replay(game_data)
                self.assertEqual(game.ply, len(game_data["moves"]))

    def test_every_game_lands_on_its_final_position(self):
        """Le test le plus fort : des centaines de coups, une seule FEN possible."""
        for game_data in GAMES:
            with self.subTest(game=game_data["id"]):
                self.assertEqual(
                    replay(game_data).current_position.to_fen(),
                    game_data["final_fen"],
                )

    def test_the_verdict_matches(self):
        for game_data in GAMES:
            with self.subTest(game=game_data["id"]):
                game = replay(game_data)
                expected = STATUS_BY_NAME[game_data["final_status"]]
                if expected is Status.ONGOING:
                    # abandon ou nulle convenue : l'échiquier ne tranche pas,
                    # mais il ne doit pas inventer une fin non plus
                    self.assertNotIn(
                        game.status(), (Status.CHECKMATE, Status.STALEMATE)
                    )
                else:
                    self.assertIs(game.status(), expected)

    def test_a_game_won_on_the_board_reports_its_winner(self):
        mated = [g for g in GAMES if g["final_status"] == "checkmate"]
        self.assertTrue(mated, "le corpus doit contenir au moins un mat")
        for game_data in mated:
            with self.subTest(game=game_data["id"]):
                self.assertEqual(replay(game_data).result(), game_data["result"])


class TestTheRulesAreActuallyExercised(unittest.TestCase):
    """Les étiquettes du corpus doivent correspondre à ce qui se joue vraiment."""

    def moves_of(self, rule):
        for game_data in GAMES:
            if rule in game_data["covers"]:
                return game_data
        self.fail(f"aucune partie ne couvre {rule}")

    def walk(self, game_data):
        """Rejoue en livrant, à chaque coup, la pièce déplacée et l'après."""
        game = Game(auto_draw=False)
        for text in game_data["moves"]:
            before = game.current_position
            move = next(m for m in before.legal_moves() if str(m) == text)
            yield before.piece_at(move.square_from), move, game.play(move)

    def test_a_promotion_really_replaces_the_pawn(self):
        seen = 0
        for piece, move, after in self.walk(self.moves_of("underpromotion")):
            if move.promotion is None:
                continue
            seen += 1
            self.assertEqual(piece.name, "pawn")
            arrived = after.piece_at(move.square_to)
            self.assertEqual(arrived.name, move.promotion)
            self.assertEqual(arrived.color, piece.color)
        self.assertGreater(seen, 0, "cette partie devait contenir une promotion")

    def test_a_castle_really_moves_two_pieces(self):
        seen = 0
        for piece, move, after in self.walk(self.moves_of("O-O-O")):
            if piece.name != "king" or abs(move.square_to[1] - move.square_from[1]) != 2:
                continue
            seen += 1
            row = move.square_from[0]
            # la tour a sauté de l'autre côté du roi
            rook_column = 3 if move.square_to[1] == 2 else 5
            corner = 0 if move.square_to[1] == 2 else 7
            self.assertEqual(after.piece_at((row, rook_column)).name, "rook")
            self.assertIsNone(after.piece_at((row, corner)))
        self.assertGreater(seen, 0, "cette partie devait contenir un roque")

    def test_an_en_passant_capture_removes_a_pawn_beside_the_landing_square(self):
        seen = 0
        for piece, move, after in self.walk(self.moves_of("en_passant")):
            if piece.name != "pawn" or move.square_from[1] == move.square_to[1]:
                continue
            if after.piece_at(move.square_to) is None:
                continue
            # prise en diagonale : si la case d'arrivée était vide avant, c'est
            # une prise en passant, et le pion mangé était à côté
            row_behind = move.square_from[0]
            if after.piece_at((row_behind, move.square_to[1])) is None:
                seen += 1
        self.assertGreater(seen, 0, "cette partie devait contenir une prise")

    def test_a_repetition_is_seen_where_the_oracle_saw_it(self):
        """Les deux politiques, sur la partie que les joueurs ont poursuivie.

        Le demi-coup vient de l'oracle : l'y retrouver croise notre détection
        de répétition avec la sienne, sur une partie réelle.
        """
        game_data = self.moves_of("repetition_played_through")
        ply = game_data["repetition_ply"]
        self.assertIsNotNone(ply)
        self.assertLess(ply, len(game_data["moves"]), "la partie doit continuer après")

        # permissif : le moteur suit les joueurs jusqu'au bout
        self.assertEqual(replay(game_data).ply, len(game_data["moves"]))

        # strict : il s'arrête exactement là où la position revient une 3e fois
        strict = Game()
        for text in game_data["moves"][:ply]:
            strict.play_text(text)
        self.assertEqual(strict.repetition_count(), 3)
        self.assertIs(strict.status(), Status.REPETITION)
        with self.assertRaises(ValueError):
            strict.play_text(game_data["moves"][ply])


if __name__ == "__main__":
    unittest.main()

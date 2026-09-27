"""L'API HTTP, en mémoire : la forme du contrat, vérifiée de bout en bout.

Ce qu'on valide ici, c'est ce que le front verra -- codes, corps, en-têtes --
pas la durabilité, qui arrive avec SQLite (tranche 2.3). Chaque test crée son
application et son store : aucun état ne fuit d'un cas à l'autre.

Ignorés si FastAPI n'est pas installé : le moteur doit rester testable sans
l'extra ``[api]``.
"""

import importlib.util
import subprocess
import sys
import threading
import unittest

HAS_API = importlib.util.find_spec("fastapi") is not None

if HAS_API:
    from fastapi.testclient import TestClient

    from chess_api.app import create_app
    from chess_api.store import InMemoryGameStore

GAMES = "/api/v1/games"
FOOLS_MATE = ["f2f3", "e7e5", "g2g4", "d8h4"]


class TestTheEngineStaysDependencyFree(unittest.TestCase):
    """La promesse du roadmap : ``import chess_engine`` ne tire rien d'autre."""

    def test_importing_the_engine_does_not_import_the_web(self):
        code = (
            "import sys, chess_engine; "
            "print(sorted(m for m in ('fastapi', 'pydantic', 'starlette') if m in sys.modules))"
        )
        output = subprocess.run(
            [sys.executable, "-c", code], capture_output=True, text=True, check=True
        ).stdout.strip()
        self.assertEqual(output, "[]")


@unittest.skipUnless(HAS_API, "extra [api] non installé")
class ApiTestCase(unittest.TestCase):
    def setUp(self):
        self.store = InMemoryGameStore()
        self.client = TestClient(create_app(self.store))

    def create(self, **body):
        response = self.client.post(GAMES, json=body)
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def play(self, game, *moves):
        """Joue une suite de coups, chacun avec le bon ``expected_ply``."""
        for move in moves:
            response = self.client.post(
                f"{GAMES}/{game['id']}/moves",
                json={"move": move, "expected_ply": game["ply"]},
            )
            self.assertEqual(response.status_code, 200, response.text)
            game = response.json()
        return game


class TestCreate(ApiTestCase):
    def test_a_default_game(self):
        response = self.client.post(GAMES, json={})
        self.assertEqual(response.status_code, 201)
        game = response.json()
        self.assertEqual(response.headers["location"], f"{GAMES}/{game['id']}")
        self.assertEqual(game["ply"], 0)
        self.assertEqual(game["status"], "ongoing")
        self.assertEqual(game["players"], {"w": "human", "b": "human"})
        self.assertIsNone(game["time_control"])
        self.assertIsNone(game["clock"])
        self.assertEqual(len(game["legal_moves"]), 20)

    def test_without_any_body(self):
        self.assertEqual(self.client.post(GAMES).status_code, 201)

    def test_the_document_has_the_contract_s_fields_in_order(self):
        game = self.create()
        self.assertEqual(
            list(game),
            ["id", "ply", "status", "result", "players", "time_control", "fen",
             "side_to_move", "in_check", "legal_moves", "moves", "san", "positions",
             "termination", "clock"],
        )

    def test_from_a_position(self):
        fen = "4k3/8/8/8/8/8/4P3/4K3 w - - 0 1"
        game = self.create(initial_fen=fen)
        self.assertEqual(game["fen"], fen)
        self.assertEqual(game["positions"], [fen])

    def test_ids_are_unpredictable_and_distinct(self):
        ids = {self.create()["id"] for _ in range(20)}
        self.assertEqual(len(ids), 20)
        for game_id in ids:
            self.assertGreaterEqual(len(game_id), 11)  # 64 bits en base64
            self.assertFalse(game_id.isdigit())

    def test_a_colliding_id_is_drawn_again_never_reused(self):
        ids = iter(["taken", "taken", "fresh"])
        client = TestClient(create_app(InMemoryGameStore(), new_id=lambda: next(ids)))
        self.assertEqual(client.post(GAMES).json()["id"], "taken")
        # le second tirage retombe sur "taken" : il est jeté, pas écrasé
        self.assertEqual(client.post(GAMES).json()["id"], "fresh")
        self.assertEqual(client.get(f"{GAMES}/taken").json()["ply"], 0)

    def test_a_time_control_is_kept(self):
        game = self.create(time_control={"base_ms": 180000, "increment_ms": 2000})
        self.assertEqual(game["time_control"], {"base_ms": 180000, "increment_ms": 2000})
        self.assertIsNone(game["clock"])  # l'horloge vient avec la tranche 2.4


class TestCreationRefusals(ApiTestCase):
    def refused(self, body, status_code=422):
        response = self.client.post(GAMES, json=body)
        self.assertEqual(response.status_code, status_code, response.text)
        return response.json()

    def test_a_bad_fen(self):
        body = self.refused({"initial_fen": "pas une fen"})
        self.assertEqual(body["error"], "invalid_fen")
        self.assertEqual(body["initial_fen"], "pas une fen")
        self.assertIn("reason", body)

    def test_an_engine_player_before_phase_5(self):
        body = self.refused({"players": {"w": "human", "b": {"engine": {"level": 3}}}})
        self.assertEqual(body, {"error": "unsupported_player", "color": "b"})

    def test_an_unknown_side(self):
        self.assertEqual(self.refused({"players": {"x": "human"}})["error"], "invalid_request")

    def test_a_bad_time_control(self):
        for time_control in [{"base_ms": 0}, {"base_ms": 60000, "increment_ms": -1}]:
            with self.subTest(time_control=time_control):
                body = self.refused({"time_control": time_control})
                self.assertEqual(body, {"error": "invalid_time_control"})

    def test_nothing_is_created_on_refusal(self):
        self.refused({"initial_fen": "pas une fen"})
        self.assertEqual(self.store._records, {})


class TestGet(ApiTestCase):
    def test_returns_the_same_document(self):
        game = self.play(self.create(), "e2e4")
        self.assertEqual(self.client.get(f"{GAMES}/{game['id']}").json(), game)

    def test_an_unknown_game(self):
        response = self.client.get(f"{GAMES}/nope")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"error": "game_not_found", "id": "nope"})


class TestPlay(ApiTestCase):
    def test_a_move_advances_the_game(self):
        game = self.play(self.create(), "e2e4", "e7e5", "g1f3")
        self.assertEqual(game["ply"], 3)
        self.assertEqual(game["moves"], ["e2e4", "e7e5", "g1f3"])
        self.assertEqual(game["san"], ["e4", "e5", "Nf3"])
        self.assertEqual(game["side_to_move"], "b")
        self.assertEqual(len(game["positions"]), 4)

    def test_a_mate_ends_it(self):
        game = self.play(self.create(), *FOOLS_MATE)
        self.assertEqual(game["status"], "checkmate")
        self.assertEqual(game["result"], "0-1")
        self.assertEqual(game["legal_moves"], [])

    def test_an_illegal_move_returns_the_game(self):
        game = self.create()
        response = self.client.post(
            f"{GAMES}/{game['id']}/moves", json={"move": "e2e5", "expected_ply": 0}
        )
        self.assertEqual(response.status_code, 422)
        body = response.json()
        self.assertEqual(body["error"], "illegal_move")
        self.assertEqual(body["move"], "e2e5")
        self.assertEqual(body["game"], game)  # rien n'a bougé

    def test_a_stale_ply_is_refused_with_the_current_game(self):
        game = self.play(self.create(), "e2e4")
        response = self.client.post(
            f"{GAMES}/{game['id']}/moves", json={"move": "e7e5", "expected_ply": 0}
        )
        self.assertEqual(response.status_code, 409)
        body = response.json()
        self.assertEqual(body["error"], "stale_ply")
        self.assertEqual((body["expected_ply"], body["actual_ply"]), (0, 1))
        self.assertEqual(body["game"], game)

    def test_replaying_the_same_request_cannot_play_twice(self):
        game = self.create()
        request = {"move": "e2e4", "expected_ply": 0}
        first = self.client.post(f"{GAMES}/{game['id']}/moves", json=request)
        second = self.client.post(f"{GAMES}/{game['id']}/moves", json=request)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 409)
        self.assertEqual(second.json()["game"]["ply"], 1)

    def test_a_finished_game_refuses_with_game_over_not_illegal_move(self):
        game = self.play(self.create(), *FOOLS_MATE)
        response = self.client.post(
            f"{GAMES}/{game['id']}/moves", json={"move": "a2a3", "expected_ply": 4}
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"], "game_over")
        self.assertEqual(response.json()["status"], "checkmate")

    def test_an_unknown_game(self):
        response = self.client.post(
            f"{GAMES}/nope/moves", json={"move": "e2e4", "expected_ply": 0}
        )
        self.assertEqual(response.status_code, 404)

    def test_a_malformed_body_gets_a_machine_code_too(self):
        game = self.create()
        response = self.client.post(f"{GAMES}/{game['id']}/moves", json={"move": "e2e4"})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["error"], "invalid_request")

    def test_two_simultaneous_moves_cannot_both_pass_the_guard(self):
        """La garde ``expected_ply`` n'a de sens que si « vérifier puis jouer » est atomique."""
        game = self.create()
        barrier = threading.Barrier(8)
        codes = []

        def post(move):
            barrier.wait()
            response = self.client.post(
                f"{GAMES}/{game['id']}/moves", json={"move": move, "expected_ply": 0}
            )
            codes.append(response.status_code)

        moves = ["e2e4", "d2d4", "g1f3", "c2c4", "b1c3", "e2e3", "d2d3", "g2g3"]
        threads = [threading.Thread(target=post, args=(move,)) for move in moves]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(sorted(codes), [200] + [409] * 7)
        self.assertEqual(self.client.get(f"{GAMES}/{game['id']}").json()["ply"], 1)


class TestResign(ApiTestCase):
    def test_ends_the_game_at_once(self):
        game = self.play(self.create(), "e2e4")
        response = self.client.post(f"{GAMES}/{game['id']}/resign", json={"color": "b"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "resignation")
        self.assertEqual(body["result"], "1-0")
        self.assertEqual(body["termination"]["by"], "b")
        self.assertEqual(body["legal_moves"], [])

    def test_needs_no_expected_ply(self):
        """L'intention d'abandonner ne dépend pas du coup que l'adversaire vient de jouer."""
        game = self.create()
        self.play(game, "e2e4")
        response = self.client.post(f"{GAMES}/{game['id']}/resign", json={"color": "w"})
        self.assertEqual(response.status_code, 200)

    def test_an_unknown_color(self):
        game = self.create()
        response = self.client.post(f"{GAMES}/{game['id']}/resign", json={"color": "white"})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["error"], "unknown_color")
        self.assertEqual(response.json()["color"], "white")

    def test_twice(self):
        game = self.create()
        self.client.post(f"{GAMES}/{game['id']}/resign", json={"color": "w"})
        response = self.client.post(f"{GAMES}/{game['id']}/resign", json={"color": "b"})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"], "game_over")
        self.assertEqual(response.json()["status"], "resignation")

    def test_then_no_move_is_accepted(self):
        game = self.create()
        self.client.post(f"{GAMES}/{game['id']}/resign", json={"color": "w"})
        response = self.client.post(
            f"{GAMES}/{game['id']}/moves", json={"move": "e2e4", "expected_ply": 0}
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"], "game_over")


if __name__ == "__main__":
    unittest.main()

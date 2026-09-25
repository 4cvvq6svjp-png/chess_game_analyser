"""L'API HTTP : quatre endpoints autour du moteur, et rien d'autre.

Tout ce qui décide vit ailleurs. Les règles sont dans ``chess_engine``, la
forme du document dans ``chess_engine.game_document``, la garde de chaque
endpoint dans ``docs/api-contract.md``, §4, que ce module suit étape par
étape. Ce qui reste ici, c'est la traduction : une requête en appel au
moteur, un refus typé en code HTTP.

    uvicorn chess_api.app:app --reload
"""

import secrets
from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from chess_engine import (
    Game,
    GameOver,
    IllegalMove,
    InvalidFen,
    UnknownColor,
    game_document,
)
from chess_engine.game_position import STARTING_FEN

from .store import (
    HUMAN,
    DuplicateGameId,
    GameNotFound,
    GameRecord,
    GameStore,
    InMemoryGameStore,
    TimeControl,
)

PREFIX = "/api/v1"

#: Combien d'identifiants tirer avant d'abandonner. Sur 64 bits, une seule
#: collision est déjà improbable ; en voir cinq de suite trahit un tirage
#: cassé, pas la malchance.
MAX_ID_ATTEMPTS = 5


def generate_id() -> str:
    """Un identifiant imprédictible : c'est le seul justificatif d'accès (contrat §3)."""
    return secrets.token_urlsafe(8)


# --- Les corps de requête -------------------------------------------------


class TimeControlBody(BaseModel):
    base_ms: int
    increment_ms: int = 0


class CreateGameBody(BaseModel):
    initial_fen: str = STARTING_FEN
    auto_draw: bool = True
    players: dict[str, Any] = {"w": HUMAN, "b": HUMAN}
    time_control: TimeControlBody | None = None


class PlayMoveBody(BaseModel):
    move: str
    expected_ply: int


class ResignBody(BaseModel):
    color: str


# --- Les refus ------------------------------------------------------------


class ApiError(Exception):
    """Un refus déjà mis en forme : un code HTTP et le corps du contrat (§7)."""

    def __init__(self, status_code: int, error: str, **payload):
        self.status_code = status_code
        self.body = {"error": error, **payload}


def document(game_id: str, record: GameRecord) -> dict:
    """Le document de partie du contrat (§5) : le moteur, plus ce que sait l'application."""
    game_part = game_document(record.game)
    time_control = record.time_control
    return {
        "id": game_id,
        "ply": game_part.pop("ply"),
        "status": game_part.pop("status"),
        "result": game_part.pop("result"),
        "players": record.players,
        "time_control": None if time_control is None else {
            "base_ms": time_control.base_ms,
            "increment_ms": time_control.increment_ms,
        },
        **game_part,
        # L'horloge arrive avec la tranche 2.4 ; le champ existe déjà pour que
        # le front n'ait pas à gérer son absence.
        "clock": None,
    }


def validate_players(players: dict[str, Any]) -> dict[str, Any]:
    """Deux camps, chacun humain. Un moteur est refusé tant que la phase 5 n'existe pas."""
    unknown = set(players) - {"w", "b"}
    if unknown:
        raise ApiError(422, "invalid_request", detail=f"camps inconnus : {sorted(unknown)}")
    complete = {"w": HUMAN, "b": HUMAN, **players}
    for color in ("w", "b"):
        if complete[color] != HUMAN:
            raise ApiError(422, "unsupported_player", color=color)
    return complete


def validate_time_control(body: TimeControlBody | None) -> TimeControl | None:
    if body is None:
        return None
    if body.base_ms <= 0 or body.increment_ms < 0:
        raise ApiError(422, "invalid_time_control")
    return TimeControl(body.base_ms, body.increment_ms)


# --- L'application --------------------------------------------------------


def create_app(store: GameStore | None = None, new_id=generate_id) -> FastAPI:
    """Une application neuve. Les tests en créent une par cas, avec leur propre store."""
    store = InMemoryGameStore() if store is None else store
    app = FastAPI(title="chess_game_analyser")

    @app.exception_handler(ApiError)
    def api_error(_: Request, error: ApiError):
        return JSONResponse(error.body, status_code=error.status_code)

    @app.exception_handler(RequestValidationError)
    def invalid_request(_: Request, error: RequestValidationError):
        # Un corps mal formé -- champ manquant, mauvais type -- reçoit lui
        # aussi un code machine, pour que tous les refus aient la même forme.
        return JSONResponse(
            {"error": "invalid_request", "detail": jsonable_encoder(error.errors())},
            status_code=422,
        )

    def load(game_id: str) -> GameRecord:
        try:
            return store.get(game_id)
        except GameNotFound:
            raise ApiError(404, "game_not_found", id=game_id) from None

    @app.post(f"{PREFIX}/games", status_code=201)
    def create_game(body: CreateGameBody | None = None):
        body = CreateGameBody() if body is None else body
        players = validate_players(body.players)
        time_control = validate_time_control(body.time_control)
        try:
            game = Game(initial_fen=body.initial_fen, auto_draw=body.auto_draw)
        except InvalidFen as error:
            raise ApiError(422, "invalid_fen", initial_fen=error.fen, reason=error.reason) from None

        record = GameRecord(game, players, time_control)
        for _ in range(MAX_ID_ATTEMPTS):
            game_id = new_id()
            try:
                store.create(game_id, record)
                break
            except DuplicateGameId:
                continue  # retirer, ne jamais réutiliser (contrat §3)
        else:
            raise RuntimeError("impossible de tirer un identifiant libre")

        return JSONResponse(
            document(game_id, record),
            status_code=201,
            headers={"Location": f"{PREFIX}/games/{game_id}"},
        )

    @app.get(f"{PREFIX}/games/{{game_id}}")
    def get_game(game_id: str):
        record = load(game_id)
        with record.lock:
            return document(game_id, record)

    @app.post(f"{PREFIX}/games/{{game_id}}/moves")
    def play_move(game_id: str, body: PlayMoveBody):
        record = load(game_id)
        with record.lock:
            game = record.game
            if body.expected_ply != game.ply:
                raise ApiError(
                    409, "stale_ply",
                    expected_ply=body.expected_ply, actual_ply=game.ply,
                    game=document(game_id, record),
                )
            side = game.current_position.side_to_move
            if record.players[side] != HUMAN:
                raise ApiError(409, "not_your_turn", side_to_move=side,
                               game=document(game_id, record))
            try:
                game.play_text(body.move)
            except GameOver as error:
                raise ApiError(409, "game_over", status=error.status.value,
                               game=document(game_id, record)) from None
            except IllegalMove as error:
                raise ApiError(422, "illegal_move", move=error.move,
                               game=document(game_id, record)) from None
            store.save(game_id, record)
            return document(game_id, record)

    @app.post(f"{PREFIX}/games/{{game_id}}/resign")
    def resign(game_id: str, body: ResignBody):
        # Pas d'expected_ply : l'abandon vaut à n'importe quel demi-coup (contrat §4).
        record = load(game_id)
        with record.lock:
            try:
                record.game.resign(body.color)
            except UnknownColor as error:
                raise ApiError(422, "unknown_color", color=error.color,
                               game=document(game_id, record)) from None
            except GameOver as error:
                raise ApiError(409, "game_over", status=error.status.value,
                               game=document(game_id, record)) from None
            store.save(game_id, record)
            return document(game_id, record)

    return app


app = create_app()

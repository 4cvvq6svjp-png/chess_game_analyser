"""Fabrique le corpus de parties rejouées : tests/data/replayed_games.json.

Pourquoi un outil séparé plutôt qu'un test qui télécharge : le corpus doit
être figé dans le dépôt. Un test qui dépend du réseau échoue pour des raisons
qui n'ont rien à voir avec les échecs, et un corpus qui change tout seul ne
prouve plus rien.

Pourquoi ``python-chess`` : convertir les parties avec notre propre moteur
serait circulaire. Un coup mal généré produirait des données fausses, que le
moteur rejouerait sans broncher. L'oracle fournit donc la notation longue, le
SAN, la FEN finale et le verdict ; notre moteur n'intervient qu'à la
vérification, et il doit retomber exactement dessus.

    pip install chess
    python tools/build_game_corpus.py

Le script a besoin du réseau. Il n'est jamais exécuté par la CI.
"""

from __future__ import annotations

import collections
import io
import json
import pathlib
import sys
import urllib.request
import zipfile

try:
    import chess
    import chess.pgn
except ImportError:  # pragma: no cover - outil, pas code de production
    sys.exit("Il faut python-chess pour régénérer le corpus : pip install chess")

DESTINATION = pathlib.Path(__file__).resolve().parents[1] / "tests/data/replayed_games.json"

#: Archives de parties historiques, au format PGN.
ARCHIVES = {
    "Morphy": "https://www.pgnmentor.com/players/Morphy.zip",
    "Alekhine": "https://www.pgnmentor.com/players/Alekhine.zip",
    # Le pat est rare à haut niveau : aucun chez Morphy ni Alekhine, deux chez
    # Karpov sur 3 500 parties. L'archive n'est là que pour lui.
    "Karpov": "https://www.pgnmentor.com/players/Karpov.zip",
}

#: Les règles à couvrir, de la plus rare à la plus commune : le recouvrement
#: glouton commence par celles qu'on ne trouve presque jamais.
TARGETS = [
    "stalemate",
    "underpromotion",
    "repetition_played_through",
    "en_passant",
    "promotion",
    "O-O-O",
    "O-O",
    "checkmate",
]


def fetch(url: str) -> str:
    # pgnmentor refuse l'agent par défaut de urllib ; on se présente.
    request = urllib.request.Request(  # noqa: S310
        url, headers={"User-Agent": "chess-game-analyser/corpus-builder"}
    )
    with urllib.request.urlopen(request, timeout=120) as response:  # noqa: S310
        archive = zipfile.ZipFile(io.BytesIO(response.read()))
    name = next(n for n in archive.namelist() if n.endswith(".pgn"))
    return archive.read(name).decode("utf-8-sig", errors="replace")


def describe(game) -> dict | None:
    """Rejoue une partie avec l'oracle et relève ce qu'elle contient."""
    board = game.board()
    if board.fen() != chess.STARTING_FEN:
        return None  # les parties à handicap ne partent pas de la position initiale

    moves, sans, covers = [], [], set()
    # L'EPD est la position plus les droits et l'en passant : la clé de la
    # répétition. On compte les visites pour repérer les parties qui ont
    # franchi une triple répétition sans que personne ne réclame la nulle.
    visits = collections.Counter([board.epd()])
    repetition_ply = None
    try:
        for move in game.mainline_moves():
            if board.is_kingside_castling(move):
                covers.add("O-O")
            if board.is_queenside_castling(move):
                covers.add("O-O-O")
            if board.is_en_passant(move):
                covers.add("en_passant")
            if move.promotion:
                covers.add("promotion")
                if move.promotion != chess.QUEEN:
                    covers.add("underpromotion")
            sans.append(board.san(move))  # avant push : le SAN se lit sur la position de départ
            board.push(move)
            moves.append(move.uci())
            visits[board.epd()] += 1
            if repetition_ply is None and visits[board.epd()] >= 3:
                repetition_ply = len(moves)
    except (ValueError, AssertionError):
        return None  # score de partie corrompu dans l'archive

    # Une triple répétition *suivie d'autres coups* : les joueurs n'ont pas
    # réclamé la nulle et ont continué. Une partie qui s'arrête pile sur la
    # troisième occurrence ne prouve rien -- c'est le comportement par défaut.
    if repetition_ply is not None and repetition_ply < len(moves):
        covers.add("repetition_played_through")

    if len(moves) < 4:
        return None
    if board.is_checkmate():
        covers.add("checkmate")
    if board.is_stalemate():
        covers.add("stalemate")

    headers = game.headers
    return {
        "white": headers.get("White", "?"),
        "black": headers.get("Black", "?"),
        "date": headers.get("Date", "?"),
        "event": headers.get("Event", "?"),
        "result": headers.get("Result", "*"),
        "covers": sorted(covers),
        # le demi-coup où une position atteint sa troisième visite, s'il existe
        "repetition_ply": repetition_ply,
        "moves": moves,
        # la notation de l'oracle, pour vérifier l'écriture du SAN de notre moteur
        "san": sans,
        # en_passant="fen" : python-chess n'écrit la case que si la prise est
        # possible, la FEN standard l'écrit après tout bond. C'est notre
        # convention qu'on veut comparer.
        "final_fen": board.fen(en_passant="fen"),
        "final_status": (
            "checkmate" if board.is_checkmate()
            else "stalemate" if board.is_stalemate()
            else "ongoing"  # abandon ou nulle convenue : l'échiquier ne tranche pas
        ),
    }


def select(catalogue: list[dict]) -> list[dict]:
    """Choisit par couverture de règles, pas par notoriété."""
    chosen, covered, taken = [], set(), set()

    def take(game):
        taken.add(id(game))
        chosen.append(game)
        covered.update(game["covers"])

    for target in TARGETS:
        if target in covered:
            continue
        pool = [g for g in catalogue if target in g["covers"] and id(g) not in taken]
        if not pool:
            continue
        # celle qui apporte le plus de règles neuves, la plus courte à égalité
        take(max(pool, key=lambda g: (len(set(g["covers"]) - covered), -len(g["moves"]))))

    def add_first(pool):
        for game in pool:
            if id(game) not in taken:
                take(game)
                return

    # de la variété : la plus longue partie, une nulle, deux mats de plus
    add_first(sorted(catalogue, key=lambda g: -len(g["moves"])))
    add_first([g for g in catalogue if g["result"] == "1/2-1/2" and len(g["moves"]) > 60])
    for _ in range(2):
        add_first([g for g in catalogue
                   if "checkmate" in g["covers"] and 40 < len(g["moves"]) < 90])
    return chosen


def identifier(game: dict) -> str:
    def surname(name):
        return name.split(",")[0].strip().lower().replace(" ", "-") or "inconnu"

    return f"{surname(game['white'])}-{surname(game['black'])}-{game['date'][:4]}"


def main():
    catalogue = []
    for name, url in ARCHIVES.items():
        print(f"téléchargement de {name}...")
        handle = io.StringIO(fetch(url))
        while (game := chess.pgn.read_game(handle)) is not None:
            described = describe(game)
            if described is not None:
                described["source"] = url
                catalogue.append(described)
    print(f"{len(catalogue)} parties lues")

    chosen = select(catalogue)
    for game in chosen:
        game["id"] = identifier(game)
        print(f"  {game['id']:38} {len(game['moves']):3} demi-coups  "
              f"{game['result']:7} {','.join(game['covers'])}")

    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    DESTINATION.write_text(
        json.dumps(
            {
                "note": "Corpus figé. Régénérer avec tools/build_game_corpus.py.",
                "oracle": f"python-chess {chess.__version__}",
                "games": chosen,
            },
            indent=1,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"\n{len(chosen)} parties écrites dans {DESTINATION}")


if __name__ == "__main__":
    main()

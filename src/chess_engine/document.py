"""Le document de partie : ce que l'API renvoie, projeté depuis une ``Game``.

Le client n'a pas de moteur (``docs/api-contract.md``, §1). Tout ce qu'il
affiche doit donc lui être servi : les coups légaux pour les pastilles,
l'échec, le SAN pour la liste des coups, une FEN par demi-coup pour le
rembobinage. Ce module en fixe la forme sans rien savoir du web -- il se teste
sans serveur, et FastAPI n'aura plus qu'à le renvoyer.

Seule la partie d'échecs est ici. L'identifiant, les joueurs, la cadence et
l'horloge appartiennent à l'application ; l'API les ajoute autour.
"""

from __future__ import annotations

from .game import Game


def game_document(game: Game) -> dict:
    """La partie telle que le client la voit, sérialisable en JSON tel quel.

    ``legal_moves`` est vide dès que la partie est terminée, même si la
    position en permet encore : le front les affiche comme jouables, et une
    partie finie n'accepte plus rien. Avec ``auto_draw=False``, une nulle
    constatée laisse la partie jouable, et les coups restent servis.
    """
    position = game.current_position
    legal = position.legal_moves()
    stored = game.to_dict()
    return {
        "ply": game.ply,
        "status": game.status().value,
        "result": game.result(),
        "fen": position.to_fen(),
        "side_to_move": position.side_to_move,
        "in_check": position.is_in_check(position.side_to_move),
        "legal_moves": [] if game.is_over() else [str(move) for move in legal],
        "moves": stored["moves"],
        "san": list(game.san()),
        "positions": [p.to_fen() for p in game.positions()],
        "termination": stored["termination"],
    }

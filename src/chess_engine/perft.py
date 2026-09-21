"""perft : compter les feuilles de l'arbre des coups légaux.

``perft(position, n)`` compte les positions atteignables en ``n`` demi-coups.
Le nombre n'a aucun intérêt en soi ; ce qui compte est qu'il soit *connu*. Des
valeurs de référence sont publiées pour une poignée de positions, et un écart
d'une seule unité signale une règle fausse quelque part -- clouage manqué,
prise en passant oubliée, roque autorisé à tort.

C'est le test qui en vaut deux cents : il ne vérifie pas un cas, il vérifie la
conjonction de toutes les règles sur des dizaines de milliers de parcours.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .game_position import GamePosition


def perft(position: GamePosition, depth: int) -> int:
    """Le nombre de positions atteignables en ``depth`` demi-coups."""
    if depth <= 0:
        return 1
    moves = position.legal_moves()
    if depth == 1:
        return len(moves)
    return sum(perft(position.apply(move), depth - 1) for move in moves)


def perft_divide(position: GamePosition, depth: int) -> dict[str, int]:
    """Le compte, ventilé par coup de premier niveau.

    L'outil de diagnostic qui va avec ``perft`` : quand un total s'écarte de
    la référence, la ventilation désigne le coup fautif, et on redescend d'un
    niveau jusqu'à isoler la règle en cause.
    """
    if depth <= 0:
        return {}
    return {
        str(move): perft(position.apply(move), depth - 1)
        for move in position.legal_moves()
    }

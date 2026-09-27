"""Les refus du moteur, un type par raison.

L'API doit répondre différemment à « ce coup n'est pas légal » (422) et à
« la partie est finie » (409) : le client n'y réagit pas pareil. Les
distinguer en lisant le texte du message ne serait pas un contrat, c'est
pourquoi chaque raison a son type (``docs/api-contract.md``, §2). Le message
reste en français et reste pour les humains ; le type et les attributs sont
pour le code.

Tous héritent de ``ValueError``, et ce n'est pas un compromis : chacun
signale une valeur refusée -- un coup, une couleur, une FEN. Le code qui
attrapait déjà ``ValueError``, le terminal au premier chef, continue de
marcher sans rien savoir de ces types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .game_position import Status


class ChessError(ValueError):
    """Ce que le moteur refuse. Attraper celle-ci, c'est attraper tous ses refus."""


class IllegalMove(ChessError):
    """Le coup n'est pas jouable ici : illégal, ou mal écrit."""

    def __init__(self, move: str):
        self.move = move
        super().__init__(f"coup illégal ou mal écrit : {move!r}")


class GameOver(ChessError):
    """La partie est terminée, plus rien ne s'y joue -- ni coup, ni abandon."""

    def __init__(self, status: Status):
        self.status = status
        super().__init__(f"la partie est terminée : {status.value}")


class UnknownColor(ChessError):
    """Une couleur autre que ``"w"`` ou ``"b"``."""

    def __init__(self, color: object):
        self.color = color
        super().__init__(f"couleur inconnue : {color!r}")


class InvalidFen(ChessError):
    """Une FEN que le moteur ne sait pas lire. ``reason`` dit où elle achoppe."""

    def __init__(self, fen: str, reason: str):
        self.fen = fen
        self.reason = reason
        super().__init__(f"FEN invalide ({reason}) : {fen!r}")

"""La partie : une position de départ, une suite de coups, et rien d'autre.

Rien n'est jamais annulé. Les positions intermédiaires ne sont pas stockées,
elles se déduisent -- ``position_at(12)`` rejoue les douze premiers coups --
ce qui rend le rembobinage gratuit et fait de l'historique la seule source de
vérité.

C'est aussi ici que vit la triple répétition, seule règle qui ne se lise pas
sur une position : il faut savoir par où l'on est passé.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .game_position import STARTING_FEN, GamePosition, Status
from .move import Move

#: Le nombre d'apparitions d'une même position qui rend la partie nulle.
REPETITION_LIMIT = 3


@dataclass
class Game:
    """Une partie en cours ou terminée.

    ``moves`` ne fait que croître : jouer ajoute, rien ne retire. Reprendre un
    coup (le *takeback*) est une autre fonctionnalité, qui consistera à
    construire une partie plus courte, pas à modifier celle-ci.
    """

    initial_fen: str = STARTING_FEN
    moves: list[Move] = field(default_factory=list)

    def __post_init__(self):
        self._positions: list[GamePosition] = []
        self._rebuild()

    def _rebuild(self):
        position = GamePosition.from_fen(self.initial_fen)
        self._positions = [position]
        for move in self.moves:
            position = position.apply(move)
            self._positions.append(position)

    def positions(self) -> list[GamePosition]:
        """Toutes les positions traversées, de l'initiale à la courante.

        Recalculées si ``moves`` a changé dans le dos de ``play`` : la liste
        est un cache, l'historique reste la source.
        """
        if len(self._positions) != len(self.moves) + 1:
            self._rebuild()
        return self._positions

    def position_at(self, ply: int) -> GamePosition:
        """La position après ``ply`` demi-coups. ``ply=0`` est la position de départ."""
        positions = self.positions()
        if not -len(positions) <= ply < len(positions):
            raise IndexError(f"demi-coup {ply} hors de la partie ({len(positions) - 1})")
        return positions[ply]

    @property
    def current_position(self) -> GamePosition:
        return self.positions()[-1]

    @property
    def ply(self) -> int:
        """Le nombre de demi-coups joués."""
        return len(self.moves)

    def play(self, move: Move) -> GamePosition:
        """Joue un coup et renvoie la position obtenue.

        Une partie terminée n'accepte plus rien. La FIDE fait des cinquante
        coups et de la répétition des *réclamations*, que seuls le
        soixante-quinzième coup et la quintuple répétition rendent
        automatiques ; ce moteur tranche tout de suite. Une partie nulle est
        nulle, et ``status()`` dit laquelle.
        """
        status = self.status()
        if status.is_over():
            raise ValueError(f"la partie est terminée : {status.value}")

        position = self.current_position
        if move not in position.legal_moves():
            raise ValueError(f"coup illégal dans cette position : {move}")
        self.moves.append(move)
        self._positions.append(position.apply(move))
        return self._positions[-1]

    def play_text(self, text: str) -> GamePosition:
        """Joue un coup écrit en notation longue (« e2e4 », « e7e8q »)."""
        move = next(
            (m for m in self.current_position.legal_moves() if str(m) == text), None
        )
        if move is None:
            raise ValueError(f"coup illégal ou mal écrit : {text!r}")
        return self.play(move)

    def repetition_count(self) -> int:
        """Combien de fois la position courante est apparue, elle comprise."""
        key = self.current_position.repetition_key()
        return sum(1 for position in self.positions() if position.repetition_key() == key)

    def status(self) -> Status:
        """Le verdict de la partie.

        La position tranche d'abord -- un mat ne devient pas une nulle parce
        qu'il survient sur une position déjà vue -- puis la répétition, qui
        n'est visible que d'ici.
        """
        status = self.current_position.status()
        if status.is_over():
            return status
        if self.repetition_count() >= REPETITION_LIMIT:
            return Status.REPETITION
        return Status.ONGOING

    def result(self) -> str | None:
        """``"1-0"``, ``"0-1"``, ``"1/2-1/2"``, ou ``None`` si rien n'est joué.

        Le camp au trait est celui qui subit le mat, donc celui qui perd.
        """
        status = self.status()
        if not status.is_over():
            return None
        if status is Status.CHECKMATE:
            return "0-1" if self.current_position.side_to_move == "w" else "1-0"
        return "1/2-1/2"

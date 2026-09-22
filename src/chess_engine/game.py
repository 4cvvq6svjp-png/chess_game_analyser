"""La partie : une position de départ, une suite de coups, et rien d'autre.

Rien n'est jamais annulé. Les positions intermédiaires ne sont pas stockées,
elles se déduisent -- ``position_at(12)`` rejoue les douze premiers coups --
ce qui rend le rembobinage gratuit et fait de l'historique la seule source de
vérité.

C'est aussi ici que vit la triple répétition, seule règle qui ne se lise pas
sur une position : il faut savoir par où l'on est passé.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from .game_position import STARTING_FEN, GamePosition, Status
from .move import Move

#: Le nombre d'apparitions d'une même position qui rend la partie nulle.
REPETITION_LIMIT = 3


@dataclass(frozen=True)
class Termination:
    """Une fin décidée par un joueur, pas par l'échiquier.

    C'est un *fait enregistré*, pas une déduction : contrairement au mat ou au
    pat, rien dans la position ne permettrait de la retrouver. D'où l'instant,
    qui n'est pas décoratif -- c'est lui qui fige l'horloge. Un abandon reçu à
    14h03 arrête le temps à 14h03, pas au prochain coup, ni à la prochaine
    lecture.
    """

    status: Status
    by: str | None
    at: float


@dataclass
class Game:
    """Une partie en cours ou terminée.

    ``moves`` ne fait que croître : jouer ajoute, rien ne retire. Reprendre un
    coup (le *takeback*) est une autre fonctionnalité, qui consistera à
    construire une partie plus courte, pas à modifier celle-ci.

    ``auto_draw`` sépare l'observation de la politique. ``status()`` dit
    toujours la vérité ; ce drapeau décide seulement si ``play()`` s'y arrête.
    Par défaut oui : une partie nulle est nulle. Le mettre à ``False`` rend les
    nulles réclamables au sens de la FIDE, ce qu'il faut pour rejouer une
    partie d'archive -- les joueurs d'une répétition triple non réclamée ont
    continué, et le moteur doit pouvoir les suivre.
    """

    initial_fen: str = STARTING_FEN
    moves: list[Move] = field(default_factory=list)
    auto_draw: bool = True
    termination: Termination | None = None

    def __post_init__(self):
        self._positions: list[GamePosition] = []
        self._keys: list[str] = []
        self._rebuild()

    def _rebuild(self):
        position = GamePosition.from_fen(self.initial_fen)
        self._positions = [position]
        self._keys = [position.repetition_key()]
        for move in self.moves:
            position = position.apply(move)
            self._positions.append(position)
            self._keys.append(position.repetition_key())

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

        Une partie terminée n'accepte plus rien. Mat et pat arrêtent toujours,
        faute de coup à jouer ; les nulles de compteur et de répétition
        n'arrêtent que si ``auto_draw`` est vrai, ce qui est le cas par défaut.
        """
        position = self.current_position
        return self._play(move, position, position.legal_moves())

    def play_text(self, text: str) -> GamePosition:
        """Joue un coup écrit en notation longue (« e2e4 », « e7e8q »)."""
        position = self.current_position
        legal = position.legal_moves()
        move = next((m for m in legal if str(m) == text), None)
        if move is None:
            raise ValueError(f"coup illégal ou mal écrit : {text!r}")
        return self._play(move, position, legal)

    def resign(self, color: str, at: float | None = None) -> Status:
        """Le camp ``color`` abandonne. Prend effet immédiatement.

        « Immédiatement » au sens fort : la fin est inscrite sur la partie, pas
        déduite de la position. Toute lecture ultérieure de ``status()`` la
        rend sans rien recalculer, sans attendre qu'on tente un coup. Une
        requête d'API qui appelle ceci a terminé la partie quand elle rend la
        main, et ``at`` marque l'instant où l'horloge s'arrête.
        """
        if color not in ("w", "b"):
            raise ValueError(f"couleur inconnue : {color!r}")
        if self.is_over():
            raise ValueError(f"la partie est déjà terminée : {self.status().value}")
        self.termination = Termination(
            Status.RESIGNATION, by=color, at=time.time() if at is None else at
        )
        return self.termination.status

    def is_over(self) -> bool:
        """Plus rien ne peut se jouer ici.

        Distinct de ``status().is_over()`` : avec ``auto_draw=False``, une
        partie peut être signalée nulle tout en restant jouable.
        """
        status = self.status()
        return status.is_over() and (self.auto_draw or not status.is_draw())

    def _play(self, move, position, legal):
        """Le corps commun, qui ne génère les coups légaux qu'une fois.

        Les deviner, trancher le verdict et valider posent la même question à
        la position ; y répondre trois fois coûtait trois fois le prix.
        """
        status = self._status_of(position, legal)
        if status.is_over() and (self.auto_draw or not status.is_draw()):
            raise ValueError(f"la partie est terminée : {status.value}")
        if move not in legal:
            raise ValueError(f"coup illégal dans cette position : {move}")

        self.moves.append(move)
        self._positions.append(position.apply(move))
        self._keys.append(self._positions[-1].repetition_key())
        return self._positions[-1]

    def repetition_count(self) -> int:
        """Combien de fois la position courante est apparue, elle comprise.

        Les clés sont calculées une fois, au moment où la position naît. Les
        recalculer à chaque appel rendait le coût quadratique en longueur de
        partie, pour un résultat identique -- une position ne change pas.
        """
        self.positions()  # rafraîchit le cache si ``moves`` a bougé de l'extérieur
        return self._keys.count(self._keys[-1])

    def status(self) -> Status:
        """Le verdict de la partie.

        Une fin enregistrée l'emporte sur tout : elle est déjà survenue, il n'y
        a rien à recalculer. C'est aussi ce qui la rend immédiate -- la lecture
        n'attend pas qu'un coup soit tenté.

        Sinon la position tranche -- un mat ne devient pas une nulle parce
        qu'il survient sur une position déjà vue -- puis la répétition, qui
        n'est visible que d'ici.
        """
        return self._status_of(self.current_position, None)

    def _status_of(self, position: GamePosition, legal: list[Move] | None) -> Status:
        # La fin enregistrée est consultée ici, et non dans ``status()``, pour
        # que *tous* les chemins la voient -- ``play()`` passe par là sans
        # appeler ``status()``, et laisserait sinon jouer une partie abandonnée.
        if self.termination is not None:
            return self.termination.status
        status = position.status(legal)
        if status.is_over():
            return status
        if self.repetition_count() >= REPETITION_LIMIT:
            return Status.REPETITION
        return Status.ONGOING

    def result(self) -> str | None:
        """``"1-0"``, ``"0-1"``, ``"1/2-1/2"``, ou ``None`` si rien n'est joué.

        Deux façons de perdre, et le perdant ne se lit pas au même endroit :
        au mat c'est le camp au trait, qui le subit ; à l'abandon c'est celui
        qui l'a demandé, quel que soit le trait.
        """
        status = self.status()
        if not status.is_over():
            return None
        if status is Status.RESIGNATION:
            return "0-1" if self.termination.by == "w" else "1-0"
        if status is Status.CHECKMATE:
            return "0-1" if self.current_position.side_to_move == "w" else "1-0"
        return "1/2-1/2"

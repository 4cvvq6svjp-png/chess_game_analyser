"""L'interface terminal : dessiner, lire une ligne, annoncer. Aucune règle ici.

Tout ce qui relève des échecs est demandé au moteur -- les coups jouables, la
légalité, la fin de partie. Ce module ne sait rien d'autre que mettre un
échiquier en caractères et interpréter « e2/e4 ».

Les entrées et sorties sont injectables : ``TerminalGame`` reçoit de quoi lire
et de quoi écrire, ce qui permet de jouer une partie entière dans un test sans
piloter l'entrée standard.
"""

from __future__ import annotations

from .game import Game
from .game_position import LETTERS_BY_NAME, STARTING_FEN, GamePosition, Status
from .move import Move, square_from_name

FILES = "abcdefgh"
COLOR_NAMES = {"w": "White", "b": "Black"}

#: Le message de fin, par verdict. ``{winner}`` n'est utilisé que par le mat.
OUTCOMES = {
    Status.CHECKMATE: "Checkmate -- {winner} wins",
    Status.STALEMATE: "Stalemate -- draw",
    Status.FIFTY_MOVE: "Fifty-move rule -- draw",
    Status.REPETITION: "Threefold repetition -- draw",
    Status.INSUFFICIENT_MATERIAL: "Insufficient material -- draw",
}


def render(position: GamePosition) -> str:
    """L'échiquier en texte, vu des blancs, avec ses rangées et ses colonnes.

    Les colonnes sont indiquées parce que c'est ainsi qu'on saisit un coup :
    l'affichage parle la même langue que l'entrée.
    """
    lines = []
    for row in range(8):
        cells = []
        for col in range(8):
            piece = position.board[row][col]
            if piece is None:
                cells.append(".")
            else:
                letter = LETTERS_BY_NAME[piece.name]
                cells.append(letter if piece.color == "w" else letter.lower())
        lines.append(f"{8 - row} | " + " ".join(cells) + " |")
    lines.append("    " + " ".join(FILES))
    return "\n".join(lines)


def parse_squares(text: str) -> tuple[tuple[int, int], tuple[int, int]]:
    """``"e2/e4"`` -> ``((6, 4), (4, 4))``.

    Ne dit rien de la légalité : elle lit deux cases, c'est tout. Savoir si le
    coup se joue est l'affaire du moteur.
    """
    parts = text.strip().lower().split("/")
    if len(parts) != 2:
        raise ValueError("Un coup s'écrit 'case/case', par exemple 'e2/e4'.")
    return square_from_name(parts[0]), square_from_name(parts[1])


class TerminalGame:
    """Une partie jouée à deux sur le même terminal."""

    def __init__(self, initial_fen: str = STARTING_FEN, read=input, write=print):
        self.game = Game(initial_fen=initial_fen)
        self._read = read
        self._write = write

    def run(self) -> Status:
        """Joue jusqu'à la fin de la partie et renvoie le verdict."""
        while self.game.status() is Status.ONGOING:
            self._show()
            try:
                move = self._ask_for_move()
            except ValueError as error:
                self._write(str(error))
                continue
            except EOFError:
                self._write("Partie interrompue.")
                return self.game.status()
            self.game.play(move)

        self._show()
        self._write(self._outcome())
        return self.game.status()

    def _show(self):
        position = self.game.current_position
        self._write(render(position))
        if (
            self.game.status() is Status.ONGOING
            and position.is_in_check(position.side_to_move)
        ):
            self._write("CHECK!")

    def _ask_for_move(self) -> Move:
        position = self.game.current_position
        text = self._read(
            f"{COLOR_NAMES[position.side_to_move]} to play (ex: 'e2/e4') : "
        )
        square_from, square_to = parse_squares(text)

        candidates = [
            move
            for move in position.legal_moves()
            if move.square_from == square_from and move.square_to == square_to
        ]
        if not candidates:
            raise ValueError("Ce coup n'est pas jouable. Essaie autre chose.")
        if len(candidates) == 1:
            return candidates[0]
        # Plusieurs coups pour un même déplacement : c'est une promotion.
        return self._ask_for_promotion(candidates)

    def _ask_for_promotion(self, candidates: list[Move]) -> Move:
        by_name = {move.promotion: move for move in candidates}
        answer = self._read(f"Promotion ({', '.join(sorted(by_name))}) : ")
        chosen = by_name.get(answer.strip().lower())
        if chosen is None:
            raise ValueError("Pièce inconnue.")
        return chosen

    def _outcome(self) -> str:
        status = self.game.status()
        loser = self.game.current_position.side_to_move
        winner = COLOR_NAMES["b" if loser == "w" else "w"]
        return f"{OUTCOMES[status].format(winner=winner)}  [{self.game.result()}]"

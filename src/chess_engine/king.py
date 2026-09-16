from typing import TYPE_CHECKING

from .move_utility import MoveUtility
from .pieces import ALL_DIRECTIONS, Piece

if TYPE_CHECKING:
    from collections.abc import Iterator

    from .chess_board import Board
    from .game_position import GamePosition
    from .move import Move


class King(Piece):
    #: Le roi va dans les huit directions, mais d'un seul pas.
    DIRECTIONS = ALL_DIRECTIONS

    def __init__(self, color) :
        super().__init__(color, "king")


    def pseudo_moves(self, position: 'GamePosition', square: tuple) -> 'Iterator[Move]':
        """Produit les huit pas du roi depuis ``square``, sans filtre de légalité.

        C'est la seule pièce dont le générateur et ``_is_valid_move`` ne
        décrivent pas le même ensemble : le validateur refuse déjà les cases
        attaquées (il appelle ``check_diags``/``check_lines``/``check_knights``
        sur l'arrivée), ce qui est un jugement de légalité et non de géométrie.
        Le générateur produit donc un sur-ensemble, et le filtre sera appliqué
        une seule fois, dans ``GamePosition.legal_moves()``.

        Ce déplacement du filtre n'est pas cosmétique : évalué depuis la case
        d'arrivée alors que le roi occupe encore son ancienne case, le
        validateur ne voit pas les attaques qui passent à travers elle -- le
        bug « king-shadow » de la section 3 du roadmap.

        Le roque n'est pas produit ici : il déplace deux pièces et dépend des
        droits portés par la position.
        """
        return self._stepping_moves(position, square, self.DIRECTIONS)


    def _is_valid_move(self, square_from: tuple, square_to: tuple, board: 'Board'):
        BOARD = board.chessboard
        # check the length of the move
        if abs(square_to[0] - square_from[0]) > 1 or abs(square_to[1] - square_from[1]) > 1:
            return False

        rowTO, colTO = square_to

        # the landing square must not hold a friendly piece
        if BOARD[rowTO][colTO] is not None and BOARD[rowTO][colTO].color == self.color:
            return False

        return   MoveUtility.check_diags(BOARD, rowTO, colTO, self.color)["check"]\
             and MoveUtility.check_lines(BOARD, rowTO, colTO, self.color)["check"]\
             and MoveUtility.check_knights(BOARD, rowTO, colTO, self.color)["check"]



    def _move_piece(self, BOARD, square, add_or_remove):
        row, col = square
        # Change the board
        if add_or_remove == "add" :
            BOARD[row][col] = King(self.color)
        else :
            BOARD[row][col] = None


    def _can_move(self, board, square):
        ROW, COL = square
        for dr, dc in self.DIRECTIONS:
            if ROW+dr in range(8) and COL+dc in range(8) and self._is_valid_move(square, (ROW+dr, COL+dc), board):
                return True
        return False
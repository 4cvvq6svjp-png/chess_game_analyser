from typing import TYPE_CHECKING

from .move import Move
from .pieces import Piece

if TYPE_CHECKING:
    from collections.abc import Iterator

    from .chess_board import Board
    from .game_position import GamePosition



class Pawn (Piece) :
    DIRECTION = {"w": -1, "b": 1}

    #: Ce qu'un pion peut devenir en atteignant la dernière rangée.
    PROMOTION_CHOICES = ("queen", "rook", "bishop", "knight")

    def __init__(self, color) :
        super().__init__(color, "pawn")


    def starting_rank(color) :
        return 6 if color == "w" else 1


    def back_rank(color) :
        return 0 if color == "w" else 7


    def pseudo_moves(self, position: 'GamePosition', square: tuple) -> 'Iterator[Move]':
        """Produit les coups du pion depuis ``square``, sans filtre de légalité.

        Le pion est la seule pièce dont les coups ne se lisent pas entièrement
        sur la grille : la prise en passant dépend du coup précédent, que la
        position porte dans ``en_passant_square``. C'est aussi la seule dont un
        déplacement peut produire *quatre* coups -- une promotion par pièce
        possible -- là où les autres en produisent un.
        """
        row, col = square
        m = self.DIRECTION[self.color]
        forward = row + m
        if not 0 <= forward < 8:
            return

        # le pas en avant, et le bond de deux depuis la rangée de départ
        if position.board[forward][col] is None:
            yield from self._push_or_promote(square, (forward, col))
            if row == Pawn.starting_rank(self.color):
                double = row + 2 * m
                if position.board[double][col] is None:
                    yield Move(square, (double, col))

        # les deux prises en diagonale
        for dc in (-1, 1):
            landing = (forward, col + dc)
            if not 0 <= landing[1] < 8:
                continue
            target = position.piece_at(landing)
            if target is not None:
                if target.color != self.color:
                    yield from self._push_or_promote(square, landing)
            elif landing == position.en_passant_square and self._victim_is_there(position, landing):
                yield Move(square, landing)


    def _push_or_promote(self, square: tuple, landing: tuple) -> 'Iterator[Move]':
        """Un coup, ou les quatre promotions si l'arrivée est la dernière rangée."""
        if landing[0] == Pawn.back_rank(self.color):
            for piece_name in self.PROMOTION_CHOICES:
                yield Move(square, landing, piece_name)
        else:
            yield Move(square, landing)


    def _victim_is_there(self, position: 'GamePosition', landing: tuple) -> bool:
        """La case d'en passant ne vaut que si le pion à prendre est bien là.

        Il se tient à côté du pion qui capture, sur la rangée que celui-ci
        quitte -- jamais sur la case d'arrivée, d'où cette vérification à part.
        """
        victim = position.piece_at((landing[0] - self.DIRECTION[self.color], landing[1]))
        return victim is not None and victim.name == "pawn" and victim.color != self.color

    # the pawn is the only piece that moves differently if it is a take or not
    # NOTE: this function must stay pure (no board mutation): it is also called
    # speculatively (check detection, stalemate scan) on the live board.
    def _is_valid_move(self, square_from: tuple, square_to: tuple, board: 'Board'):
        BOARD = board.chessboard
        m = self.DIRECTION[self.color]
        # is it a take ?
        if abs(square_to[1] - square_from[1]) == 1 and square_to[0] - square_from[0] == m:
            landing_spot = BOARD[square_to[0]][square_to[1]]
            if landing_spot is not None and landing_spot.color != self.color:
                return True
            # is it en passant ? (the captured pawn is removed at execution time)
            if self._is_en_passant(square_from, square_to, board):
                return True

        # then it is a move forward
        if square_from[1] == square_to[1] :
            if square_to[0] - square_from[0] == m and BOARD[square_to[0]][square_to[1]] is None:
                return True
            elif square_to[0] - square_from[0] == 2*m and square_from[0] == Pawn.starting_rank(self.color)\
                and BOARD[square_to[0]][square_to[1]] is None\
                and BOARD[square_from[0] + m][square_from[1]] is None:
                return True


        return False


    def _is_en_passant(self, square_from: tuple, square_to: tuple, board: 'Board'):
        """Pure check: is this diagonal move a legal en-passant capture?"""
        BOARD = board.chessboard
        m = self.DIRECTION[self.color]
        # must be a one-square diagonal step onto an empty square
        if not (abs(square_to[1] - square_from[1]) == 1 and square_to[0] - square_from[0] == m):
            return False
        if BOARD[square_to[0]][square_to[1]] is not None:
            return False
        if not board.play_stack:
            return False
        last_move = board.play_stack[-1]
        # the last move was the enemy pawn double-pushing right beside us
        return (last_move["piece"] == "pawn"
                and abs(last_move["square_from"][0] - last_move["square_to"][0]) == 2
                and last_move["square_to"][1] == square_to[1]
                and last_move["square_to"][0] == square_from[0])


    def _execute_move(self, board: 'Board', square_from: tuple, square_to: tuple):
        # en passant: remove the captured pawn (it is not on the landing square)
        # before performing the regular move + play_stack bookkeeping.
        if self._is_en_passant(square_from, square_to, board):
            captured = board.play_stack[-1]["square_to"]
            board.chessboard[captured[0]][captured[1]] = None
        super()._execute_move(board, square_from, square_to)


    def _move_piece(self, BOARD, square, add_or_remove):
        row, col = square
        # Change the board
        if add_or_remove == "add" :
            BOARD[row][col] = Pawn(self.color)
        else :
            BOARD[row][col] = None


    def _can_move(self, board, square):
        ROW, COL = square
        dir = self.DIRECTION[self.color]
        directions = [[dir, 0], [dir, 1], [dir, -1]]
        for dr, dc in directions :
            if ROW+dr in range(8) and COL+dc in range(8) and self._is_valid_move(square, (ROW+dr, COL+dc), board):
                return True
        return False
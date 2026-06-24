from pieces import Piece

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .chess_board import Board



class Pawn (Piece) :
    DIRECTION = {"w": -1, "b": 1}

    def __init__(self, color) :
        super().__init__(color, "pawn")


    def starting_rank(color) :
        return 6 if color == "w" else 1

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
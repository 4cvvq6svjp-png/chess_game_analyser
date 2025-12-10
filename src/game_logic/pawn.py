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
    def _is_valid_move(self, square_from: tuple, square_to: tuple, board: 'Board'):
        BOARD = board.chessboard
        m = self.DIRECTION[self.color]
        # is it a take ?
        if abs(square_to[1] - square_from[1]) == 1 and square_to[0] - square_from[0] == m:
            landing_spot = BOARD[square_to[0]][square_to[1]]
            if landing_spot is not None and landing_spot.color != self.color:
                return True
            # is it en passant ?
            if board.play_stack:
                last_move = board.play_stack[-1]
                print(last_move, abs(last_move["square_from"][0] - last_move["square_to"][0]), abs(last_move["square_to"][1] - square_to[1]))
                if last_move["piece"] == "pawn"\
                    and abs(last_move["square_from"][0] - last_move["square_to"][0]) == 2\
                    and last_move["square_to"][1] == square_to[1]:
                    return True

        # then it is a move forward
        if square_from[1] == square_to[1] :
            if square_to[0] - square_from[0] == m:
                return True
            elif square_to[0] - square_from[0] == 2*m and square_from[0] == Pawn.starting_rank(self.color):
                return True
            

        return False
        

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
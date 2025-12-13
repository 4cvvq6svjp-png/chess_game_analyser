from chess_board import Board
from player import Player
from pieces import Piece

# A move is a starting square and an ending one. Then we wil check if it could be played.
# a move will be a input like this : "a1/a2", we check if the color id right with the number of turn 
# it will be parsed and transformed to be 2 tuples, a start_square and an end_square
from typing import TYPE_CHECKING
from copy import deepcopy


if TYPE_CHECKING:
    from .pieces import Piece





class chess_game ():
    COLOR = ["w", "b"]


    def __init__(self):
        self.playground = Board()
        self.turn = 0
        self.game_is_live = True
        self.players = [Player("w"), Player("b")]
        self.check = False
        self.checkmate = False
        self.stalemate = False
        self.pat = False


    def _is_white_turn(self) :
        return self.turn%2 == 0


    def coordinate(self, move) :
        start, end = move.strip().split('/')
        # we assume that both are of length 2, and return the coordinates as tuples
        return (8 - int(start[1]), int(ord(start[0]) - ord("a"))) , (8 - int(end[1]), int(ord(end[0]) - ord("a")))

    # to tell if a move is possible before checking the trajectory, we check if the starting square has a piece or not
    # then if it is of the right color and if the rows ans cols ranges are right.
    def _could_be_a_move(self, start_square, end_square):
        if start_square == end_square : return False
        row, col = start_square # When to use coordinate function ?
        row1, col1 = end_square

        # check the range
        if not (row in range(8) and col in range(8) and row1 in range(8) and col1 in range(8)):
            return False

        # check if the Piece exist at the starting square and if it has the right color
        if self.playground.chessboard[row][col] is not None:
            if (self._is_white_turn() and self.playground.chessboard[row][col].color  == "w") or\
                (not self._is_white_turn() and self.playground.chessboard[row][col].color  == "b"):
                return True
        return False


    def launch_game(self) :
        board = self.playground
        while self.game_is_live :
            curr_player = self.players[self.turn%2]
            next_player = self.players[(self.turn+1)%2]

            # Display 
            board.display_board()

            # ask for a move
            move = curr_player.tell_a_move()

            # try parsing
            try: 
                square_from, square_to = self.coordinate(move)
            except Exception:
                print("Not a valid input")
                print("Please rewrite your move")
                continue
            
            # check if it points to a Piece
            try:
                if not self._could_be_a_move(square_from, square_to) :
                    print("Your starting square is empty")
                    print("PLease try anoter input")
                    continue
            except Exception:
                print("Not a valid Move")
                print("Please rewrite your move")

            moving_piece = board.chessboard[square_from[0]][square_from[1]]


            if moving_piece._is_valid_move(square_from, square_to, board) :
                copy_board = deepcopy(board)
                moving_piece._execute_move(copy_board, square_from, square_to)
                if copy_board.is_in_check(curr_player.color)["check"] :
                    print("you must not stay or go into CHECK!")
                    continue
                
                if board._isbackrank_PawnMove(square_from, square_to):
                    while True:
                        piece_name = curr_player.tell_a_piece()
                        if piece_name in ["queen", "rook", "knight", "bishop"]:
                            new_piece = Board.create_piece_by_name(piece_name, curr_player.color)
                            break
                    moving_piece._move_piece(board.chessboard, square_from, "remove")
                    new_piece._move_piece(board.chessboard, square_to, "add")
                else:
                    moving_piece._execute_move(board, square_from, square_to)
                self.turn += 1  
            else:
                print("you cannot play this move try another one.")

            # watch for checks and checkmate
            self.check = False
            ischeck = board.is_in_check(next_player.color)
            if ischeck["check"] :
                print("CHECK!!")
                self.check = True
                if board.is_it_checkmate(next_player.color, ischeck["square_attacker"], ischeck["double_check"]):
                    self.game_is_live = False
                    self.checkmate = True
                    continue
            
            # watch for stalemate
            isstalemate = board._is_stalemate()
            if isstalemate:
                self.game_is_live = False
                self.stalemate = True
                continue

            # watch for pat
            if not self.check and self.turn > 0 and board._is_pat(next_player.color) :
                self.game_is_live = False
                self.pat = True

        board.display_board()

        if self.checkmate :
            print(f"The player : {curr_player.color} won.")
        elif self.stalemate :
            print(f"This is a STALEMATE")
        elif self.pat :
            print("This is a PAT")
                
            



            
    



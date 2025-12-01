from chess_board import Board
from player import Player
from pieces import Piece

# A move is a starting square and an ending one. Then we wil check if it could be played.
# a move will be a input like this : "a1/a2", we check if the color id right with the number of turn 
# it will be parsed and transformed to be 2 tuples, a start_square and an end_square
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .pieces import Piece





class chess_game ():
    COLOR = ["w", "b"]


    def __init__(self):
        self.playground = Board()
        self.turn = 0
        self.game_is_live = True
        self.players = [Player("w"), Player("b")]
        # let's see if i continue with this ? 
        self.check = False


    def _is_white_turn(self) :
        return self.turn[0] == self.turn[1] 


    def coordinate(self, move) :
        start, end = move.strip().split('/')
        # we assume that both are of length 2, and return the coordinates as tuples
        return (8 - int(start[1]), ord(start[0]) - ord("a")) , (8 - int(end[1]), ord(end[0]) - ord("a"))

    # to tell if a move is possible before checking the trajectory, we check if the starting square has a piece or not
    # then if it is of the right color and if the rows ans cols ranges are right.
    def _could_be_a_move(self, start_square, end_square):
        row, col = start_square # When to use coordinate function ?
        row1, col1 = end_square

        # check the range
        if not (row in range(8) and col in range(8) and row1 in range(8) and col1 in range(8)):
            return False

        # check if the Piece exist at the staring square and if it ahs the right color
        if self.playground.chessboard[row][col] is not None:
            if (self._is_white_turn() and self.playground.chessboard[row][col].color  == "w") or\
                (not self._is_white_turn() and self.playground.chessboard[row][col].color  == "b"):
                return True
        return False


    def launch_game(self) :

        while self.game_is_live :
            curr_player_color = self.players[self.turn%2]
            next_player_color = self.COLOR[(self.turn+1)%2]

            # Display 
            self.playground.display_board()

            # ask for a move
            move = curr_player_color.tell_a_move()

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

            # check if the move is possible according to the piece chosen and the current state of the board
            moving_piece = self.playground.chessboard[square_from[0]][square_from[1]]

            # TODO -- > everything is checked until here

            if moving_piece._is_valid_move(square_from, square_to) :
                # are we in check ? if yes we must see if the next move takes us out of it 
                if self.check:
                    copy_board = self.playground.chessboard.copy()
                    moving_piece._execute_move(copy_board, square_from, square_to)
                    if Board.is_in_check(copy_board, curr_player_color) :
                        break

                # then execute the move - we are sure is it not in checck anymore
                moving_piece._execute_move(self.playground.chessboard, square_from, square_to)
                self.turn += 1

            # TODO - designing how the check/checkmate mechanism would work
            if Board.is_in_check(self.playground.chessboard, next_player_color) :
                self.check = True
                if Board.is_it_checkmate(self.playground.chessboard, next_player_color):
                    self.game_is_live = False




        print(f"The player : {curr_player_color} won.")
                
            



            
    



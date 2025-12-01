from chess_board import Board
from player import Player
from pieces import Piece

# A move is a starting square and an ending one. Then we wil check if it could be played.
# a move will be a input like this : "a1/a2", we check if the color id right with the number of turn 
# it will be parsed and transformed to be 2 tuples, a start_square and an end_square
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .pieces import Piece





class chess_game():
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


    def coordinate(move) :
        start, end = move.strip().split('/')
        # we assume that both are of length 2, and return the coordinates as tuples
        return (start[1], ord("a") - ord(start[0])) , (ord("a") - ord(end[0]), end[1])

    # to tell if a move is possible before checking the trajectory, we check if the starting square has a piece or not
    # then if it is of the right color and if the rows ans cols ranges are right.
    def _could_be_a_move(self, start_square, end_square):
        row, col = start_square # When to use coordinate function ?
        row1, col1 = end_square

        # check the range
        if not (row in range(8) and col in range(8) and row1 in range(8) and col1 in range(8)):
            return False

        # check if the Piece exist at the staring square and if it ahs the right color
        if self.board[row][col] is not None:
            if (self._is_white_turn() and self.playground.chessboard[row][col].color  == "w") or\
                (not self._is_white_turn() and self.playground.chessboard[row][col].color  == "b"):
                return True
        return False

    # check/checkmate mechanism -- does it belong here ? TODO
    ## surtout comment je vais faire pour valider un move après un check? -- _is_valid_move() à modif ? 
    ## 
    def _is_it_checkmate(self):
        pass
    def is_in_check(self, color_of_king) : #check the oppostire color from the precedent move
        pass


    # pat : no move left/3 move repetition to be implemented
    # TODO 


    def launch_game(self) :
        while self.game_is_live :
            curr_player = self.players[self.turn%2]
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
            if not self._could_be_a_move(square_from) :
                print("Your starting square is empty")
                print("PLease try anoter input")
                continue

            # check if the move is possible according to the piece chosen and the current state of the board
            moving_piece = self.board.chessboard[square_from[0], square_from[1]]
            if moving_piece._is_valid_move(square_from, square_to) :
                # is the landing square taken ? -- cannot be a king because the check trigger would be triggered
                if self.board.chessboard[square_to[0], square_to[1]] is not None:
                    piece_to_remove = self.board.chessboard[square_to[0], square_to[1]]
                    piece_to_remove._move_piece(self.playground.chessboard, square_from, "remove")
                
                # then execute the move
                moving_piece.execute_move(self.playground.chessboard, square_from, square_to)
                self.turn += 1

            # TODO - designing how the check/checkmate mechanism would work
            if self.is_in_check(self.COLOR[(self.turn+1)%2]) :
                self.check = True
                if self.is_it_checkmate():
                    self.game_is_live = False

        ## Réalisation : à chaque move il faut trouver un moyen de vérifier quelles cases ne sont plus prise via "blocage"
        ## ie : un pion devant un fou ? 
        ## idée - > à chaque move, vérifier la square from et le square to en diagonale, en ligne et en L pour changer le taken_board
        ## surtout il faut que je regarde ce qui est le plus pratique entre regarder uniquement les check et checkmate à chaque tour 
        ## et faire un calcul de "blocage" ou de "take" pour voir si c'est un checkmate ? 
        ## TRES porbablement mieux que mon idée de "taken_board"


        print(f"The player : {curr_player} won.")
                
            



            
    



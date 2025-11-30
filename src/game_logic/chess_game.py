from chess_board import Board
from player import Player
from pieces import Piece

# A move is a starting square and an ending one. Then we wil check if it could be played.
# a move will be a input like this : "a1/a2", we check if the color id right with the number of turn 
# it will be parsed and transformed to be 2 tuples, a start_square and an end_square


class chess_game():
    def __init__(self):
        self.board = Board()
        self.turn = [0,0]
        self.game_is_live = True
        self.players = [Player("w"), Player("b")]


    def _is_white_turn(self) :
        return self.turn[0] == self.turn[1]


    def coordinate(move) :
        start, end = move.strip().split('/')
        # we assume that both are of length 2, and return the coordinates as tuples
        return (ord("a") - ord(start[0]), start[1]) , (ord("a") - ord(end[0]), end[1])

    # to tell if a move is possible before checking the trajectory, we check if the starting square has a piece or not
    # then if it is of the right color
    def _could_be_a_move(self, start_square):
        row, col = start_square # When to use coordinate function ? 
        if self.board[row][col] is not None:
            if (self._is_white_turn() and self.board[row][col].color  == "w") or\
                (not self._is_white_turn() and self.board[row][col].color  == "b"):
                return True
        return False
    

    def launch_game(self) :
        while self.game_is_live :

    



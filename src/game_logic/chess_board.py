import numpy as np

from pieces import Piece
from bishop import Bishop
from knight import Knight
from rook import Rook
from queen import Queen
from king import King
from pawn import Pawn 

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .pieces import Piece



class Board :
    def __init__(self):
        # how move history will be stored
        self.play_stack = []
        self.chessboard = self.init_board()
        # TODO - history of moves when going through the different variations
        self.explored_history = {}


    def init_board() :
        board = [[None for _ in range(8)] * 8]
        
        ### Init white pieces
        #init pawn
        for i in range(8) :
            board[6][i] = Pawn("w")

        #init rooks
        board[7][7] = Rook("w")
        board[7][0] = Rook("w")

        #init knights
        board[7][6] = Knight("w")
        board[7][1] = Knight("w")

        #init bishops
        board[7][5] = Bishop("w")
        board[7][2] = Bishop("w")
        
        #init Queen and king
        board[7][4] = King("w")
        board[7][3] = Queen("w")

        ### Init Black pieces
        #init pawn
        for i in range(8) :
            board[1][i] = Pawn("b")

        #init rooks
        board[2][7] = Rook("b")
        board[2][0] = Rook("b")

        #init knights
        board[2][6] = Knight("b")
        board[2][1] = Knight("b")

        #init bishops
        board[2][5] = Bishop("b")
        board[2][2] = Bishop("b")
        
        #init Queen and king
        board[2][4] = King("b")
        board[2][3] = Queen("b")

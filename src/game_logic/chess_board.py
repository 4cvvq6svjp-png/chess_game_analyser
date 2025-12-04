import numpy as np

from pieces import Piece
from bishop import Bishop
from knight import Knight
from rook import Rook
from queen import Queen
from king import King
from pawn import Pawn 
from move_utility import MoveUtility



from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .pieces import Piece



class Board :
    DIRECTION = {"w": -1, "b": 1}

    def __init__(self):
        # how move history will be stored
        self.play_stack = []
        self.chessboard: list[list['Piece']] = self.init_board()
        # TODO - history of moves when going through the different variations
        self.explored_history = {}

    # check/checkmate mechanism -- does it belong here ? TODO
    ## surtout comment je vais faire pour valider un move après un check? -- _is_valid_move() à modif ? 
    ## 
    def is_it_checkmate(BOARD, color_of_king):
        return False

    def is_in_check(BOARD, color_of_king) : #check the opposit color from the precedent move
        # find the king on the board
        stop = False
        for r in range(8) :
            for c in range(8) :
                if (BOARD[r][c] is not None) and (BOARD[r][c].name == "king")\
                    and (BOARD[r][c].color == color_of_king):
                    stop = True
                    break
            if stop :
                break
        print(MoveUtility.check_diags(BOARD, r, c, color_of_king))
        print(MoveUtility.check_lines(BOARD, r, c, color_of_king))
        print(MoveUtility.check_horses(BOARD, r, c, color_of_king))



        return not ((MoveUtility.check_diags(BOARD, r, c, color_of_king)\
                and MoveUtility.check_lines(BOARD, r, c, color_of_king)\
                and MoveUtility.check_horses(BOARD, r, c, color_of_king)))


    # pat : no move left/3 move repetition to be implemented
    # TODO 


    
    # to display the board in the Terminal 
    def display_board(self):
        for row in range(8) :
            line = ["|"]
            for col in range(8) :
                if self.chessboard[row][col] is not None:
                    p = self.chessboard[row][col]
                    name = p.name[0].upper() if p.color == "w" else p.name[0]
                    line.append(name)
                    line.append("|")
                else:
                    line.append(" ")
                    line.append("|")
            print("  ".join(line))
            print()


    def init_board(self) :
        board = [[None for _ in range(8)] for _ in range(8)]

        ### Init white pieces
        #init pawns
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
        #init pawns
        for i in range(8) :
            board[1][i] = Pawn("b")

        #init rooks
        board[0][7] = Rook("b")
        board[0][0] = Rook("b")

        #init knights
        board[0][6] = Knight("b")
        board[0][1] = Knight("b")

        #init bishops
        board[0][5] = Bishop("b")
        board[0][2] = Bishop("b")
    
        #init Queen and king
        board[0][4] = King("b")
        board[0][3] = Queen("b")
        return board
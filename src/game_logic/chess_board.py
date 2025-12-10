import numpy as np

from pieces import Piece
from bishop import Bishop
from knight import Knight
from rook import Rook
from queen import Queen
from king import King
from pawn import Pawn 
from move_utility import MoveUtility
from math import copysign



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


    def is_it_checkmate(BOARD_copy, color_of_king, attacking_piece_position, double_check):
        """Verifies if there is a checkmate."""
        print("begin check for checkmate")
        # find the king on the board
        stop = False
        for r in range(8) :
            for c in range(8) :
                if (BOARD_copy[r][c] is not None) and (BOARD_copy[r][c].name == "king")\
                    and (BOARD_copy[r][c].color == color_of_king):
                    stop = True
                    break
            if stop :
                break
        king = BOARD_copy[r][c]
        
        # can the king move ?
        for dr in [-1, 1]:
            for dc in [-1, 1]:
                if (r+dr in range(8)) and (c+dc in range(8)) and\
                    (BOARD_copy[r+dr][c+dc] is None) and\
                    (king._is_valid_move((r,c), (r+dr, c+dc), BOARD_copy)) :
                    return False
        
        row, col = attacking_piece_position
        attacker = BOARD_copy[row][col]
        print("the king cannot move")
        # If the attack is double then it is a mate
        if double_check:
            return True

        # can we eat the piece ? -- the trick is to use these function to see if a piece could be eaten or not, 
        # this is equivalent to 

        if    not  (MoveUtility.check_diags(BOARD_copy, row, col, attacker.color)["check"]\
                and MoveUtility.check_lines(BOARD_copy, row, col, attacker.color)["check"]\
                and MoveUtility.check_horses(BOARD_copy, row, col, attacker.color)["check"]):
            return False
        print("we cannot eat the piece")
        # if not a horse/pawn --> can we block it ?
        if attacker.name in ["horse", "pawn"] : return True

        inbetween_square = []
        while abs(row - r)>1 or abs(col - c)>1 :
            row += int(copysign(1, r - row)) if r!=row else 0
            col += int(copysign(1, c - col)) if c!=col else 0
            inbetween_square.append((row, col))
        print(inbetween_square)
        for dr, dc in inbetween_square :
            if not (MoveUtility.check_diags(BOARD_copy, dr, dc, attacker.color)["check"]\
                and MoveUtility.check_lines(BOARD_copy, dr, dc, attacker.color)["check"]
                and MoveUtility.check_horses(BOARD_copy, dr, dc, attacker.color)["check"]):
                print(f"we can block on this square : {(dr,dc)}")
                return False
        return True



    def is_in_check(BOARD, color_of_king) :
        """Verify if there is a check on the board"""
        stop = False
        for r in range(8) :
            for c in range(8) :
                if (BOARD[r][c] is not None) and (BOARD[r][c].name == "king")\
                    and (BOARD[r][c].color == color_of_king):
                    stop = True
                    break
            if stop :
                break

        # let's locate the checks
        checkS = [MoveUtility.check_diags(BOARD, r, c, color_of_king),
                  MoveUtility.check_lines(BOARD, r, c, color_of_king),
                  MoveUtility.check_horses(BOARD, r, c, color_of_king)]
        possible_check = [elt["check"] for elt in checkS]
        
        trues = possible_check.count(True)
        if trues == 3 :
            return {"check":False, "double_check":False,"square_attacker":(-1,-1)}
        elif trues <= 1 :
            return {"check":True, "double_check":True, "square_attacker":(-1,-1)}
        
        if not possible_check[0] :
            return {"check":True, "double_check":False, "square_attacker":checkS[0]["square_attacker"]}
        elif not possible_check[1] :
            return {"check":True, "double_check":False, "square_attacker":checkS[1]["square_attacker"]}
        elif not possible_check[2]:
            return {"check":True, "double_check":False, "square_attacker":checkS[2]["square_attacker"]}

        

    # TODO - pat

    def _is_stalemate(self) :
        if len(self.play_stack) >= 8 and self.play_stack[:4] == self.play_stack[4:] :
            return True
        return False
    
    def _is_pat(self, color) :
        for row in range(8) :
            for col in range(8) :
                if self.chessboard[row][col] and self.chessboard[row][col].color == color:
                    piece = self.chessboard[row][col]
                    if piece._can_move(self, (row,col)) :
                        return False
        return True

    
    def display_board(self):
        """To display the board in the terminal"""
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
        """To initialize the chessboard"""
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
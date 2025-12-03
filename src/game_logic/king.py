from pieces import Piece
from move_utility import MoveUtility


class King(Piece):
    DIRECTION = {"w": -1, "b": 1}

    def __init__(self, color) :
        super().__init__(color, "king")



    def _is_valid_move(self, square_from: tuple, square_to: tuple, BOARD: list[list['Piece']]):
        # check the length of the move
        if abs(square_to[0] - square_from[0]) > 1 or abs(square_to[1] - square_from[1]):
            return False

        rowTO, colTO = square_to
        m = self.DIRECTION[self.color]
        
        # check the checks in line 
        directions = [[0,1], [1,0], [0,-1], [-1,0]]
        for dr, dc in directions :
            row = rowTO
            col = colTO
            while (row + dr in range(8)) and (col + dc in range(8))\
            and (BOARD[row+dr][col+dc] is None):
                row += dr
                col += dc
            if BOARD[row][col] and (BOARD[row][col].name in ["queen", "rook"]) :
                return False
            elif BOARD[row][col] and (BOARD[row][col].name == "king") and (abs(row - rowTO) < 1 or abs(col - colTO) < 1) :
                return False
        
        #check the diags
        directions = [[1,1], [1,-1], [-1,-1], [-1,1]]
        for dr, dc in directions :
            row = rowTO
            col = colTO
            while (row + dr in range(8)) and (col + dc in range(8))\
            and (BOARD[row+dr][col+dc] is None):
                row += dr
                col += dc
            if BOARD[row][col] and BOARD[row][col].name in ["queen", "bishop"]:
                return False
            elif BOARD[row][col] and (BOARD[row][col].name == "king") and (abs(row - rowTO) < 1 or abs(col - colTO) < 1) :
                return False
            ## à verif, c'est la logique derrière une échec fait par un pion
            elif BOARD[row][col] and (BOARD[row][col].name == "pawn") and (row - rowTO == m) :
                return False

        # check the knights
        


    def _move_piece(self, BOARD, square, add_or_remove):
        row, col = square
        # Change the board
        if add_or_remove == "add" :
            BOARD[row][col] = King(self.color)
        else :
            BOARD[row][col] = None
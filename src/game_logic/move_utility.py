from math import copysign

class MoveUtility :

    def _is_diag_valid (square_from, square_to, BOARD):
        pass

    def _is_line_valid (square_from, square_to, BOARD):
        # Not a move
        if not ((square_from[0] == square_to[0]) != (square_from[1] == square_to[1])) : # XOR
            return False
        
        isvalid = True
        row, col = square_from
        rowTO, colTO = square_to

        # landing square has a same color piece on it
        if (BOARD[rowTO][colTO] is not None) and (BOARD[row][col].color == BOARD[rowTO][colTO].color) :
            return False

        # we check if the inbetween path is free or not
        while isvalid and (abs(row-rowTO) > 1 or abs(col-colTO) > 1) :
            row += int(copysign(1, rowTO - row)) if rowTO!=row else 0
            col += int(copysign(1, colTO - col)) if colTO!=col else 0
            if BOARD[row][col] is not None :
                isvalid = False
        return isvalid







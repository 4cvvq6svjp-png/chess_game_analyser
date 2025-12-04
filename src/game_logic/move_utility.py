from math import copysign

class MoveUtility :
    DIRECTION = {"w": -1, "b": 1}



    def _is_diag_valid (square_from, square_to, BOARD):
        # Not a diag move
        if abs(square_from[0] - square_to[0]) != abs(square_from[1] - square_to[1]) : # XOR
            return False
        
        isvalid = True
        row, col = square_from
        ROW, COL = square_to

        # landing square has a same color piece on it
        if (BOARD[ROW][COL] is not None) and (BOARD[row][col].color == BOARD[ROW][COL].color) :
            return False

        # we check if the inbetween path is free or not
        while isvalid and (abs(row-ROW) > 1 or abs(col-COL) > 1) :
            row += int(copysign(1, ROW - row)) if ROW!=row else 0
            col += int(copysign(1, COL - col)) if COL!=col else 0
            if BOARD[row][col] is not None :
                isvalid = False
        return isvalid




    def _is_line_valid (square_from, square_to, BOARD):
        # Not a line move
        if not ((square_from[0] == square_to[0]) != (square_from[1] == square_to[1])) : # XOR
            return False
        
        isvalid = True
        row, col = square_from
        ROW, COL = square_to

        # landing square has a same color piece on it
        if (BOARD[ROW][COL] is not None) and (BOARD[row][col].color == BOARD[ROW][COL].color) :
            return False

        # we check if the inbetween path is free or not
        while isvalid and (abs(row-ROW) > 1 or abs(col-COL) > 1) :
            row += int(copysign(1, ROW - row)) if ROW!=row else 0
            col += int(copysign(1, COL - col)) if COL!=col else 0
            if BOARD[row][col] is not None :
                isvalid = False
        return isvalid
    

    ## Check for checks

    # true if valid
    def check_diags(BOARD, ROW, COL, color) :
        m = MoveUtility.DIRECTION[color]

        #check the diags
        directions = [[1,1], [1,-1], [-1,-1], [-1,1]]
        for dr, dc in directions :
            row = ROW
            col = COL
            while (row+dr in range(8)) and (col+dc in range(8)):
                row += dr
                col += dc
                if BOARD[row][col] is not None :
                    break
            if row+dr not in range(8) or col+dc not in range(8) or not BOARD[row][col]: continue
            if BOARD[row][col].color == color : continue

            if BOARD[row][col].name in ["queen", "bishop"]:
                return False
            elif (BOARD[row][col].name == "king") and (abs(row - ROW) < 1 or abs(col - COL) < 1) :
                return False
            ## à verif, c'est la logique derrière une échec fait par un pion
            elif (BOARD[row][col].name == "pawn") and (row - ROW == m) :
                return False
        return True
    

    def check_lines(BOARD, ROW, COL, color) :
        # check the checks in line 
        directions = [[0,1], [1,0], [0,-1], [-1,0]]
        for dr, dc in directions :
            row = ROW
            col = COL
            while (row+dr in range(8)) and (col+dc in range(8)):
                row += dr
                col += dc
                if BOARD[row][col] is not None :
                    break
            if row+dr not in range(8) or col+dc not in range(8) or not BOARD[row][col]: continue
            if BOARD[row][col].color == color : continue

            if BOARD[row][col].name in ["queen", "rook"] :
                return False
            elif (BOARD[row][col].name == "king") and (abs(row - ROW) < 1 or abs(col - COL) < 1) :
                return False
        return True
    
    def check_horses(BOARD, ROW, COL, color) :
        horse_square = [[2,1], [2,-1], [-2,1], [-2,-1], [1,2], [-1,2], [1,-2], [-1,-2]]
        for dr, dc in horse_square:
            if (ROW+dr in range(8)) and (COL+dc in range(8)) and (BOARD[ROW+dr][COL+dc] is not None)\
            and BOARD[ROW+dr][COL+dc].name == "horse" and BOARD[ROW+dr][COL+dc].color != color:
                return False
        return True







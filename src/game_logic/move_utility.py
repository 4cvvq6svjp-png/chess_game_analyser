from math import copysign

class MoveUtility :
    DIRECTION = {"w": -1, "b": 1}
    first_rank = {"w":6, "b":1}

    ###############################################################
    #### Functions to be used to see if a move is valid or not ####
    ###############################################################

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
    

    #######################################################################
    #### Functions to be used to see if a square is threatened or not  ####
    #######################################################################


    def check_diags(BOARD, ROW, COL, color) :
        """Returns False if the square is threatened by its diagonals and tells where is the attacker. True if not."""
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
            
            if BOARD[row][col] is None or BOARD[row][col].color == color: continue

            if BOARD[row][col].name in ["queen", "bishop"]:
                return {"check":False, "square_attacker":(row,col)}
            elif (BOARD[row][col].name == "king") and (abs(row - ROW) <= 1 and abs(col - COL) <= 1) :
                return {"check":False, "square_attacker":(row,col)}
            ## à verif, c'est la logique derrière un échec fait par un pion
            elif (BOARD[row][col].name == "pawn") and (row - ROW == m) :
                return {"check":False, "square_attacker":(row,col)}
        return {"check":True, "square_attacker":(-1, -1)}
    

    def check_lines(BOARD, ROW, COL, color) :
        """Returns False if the square is threatened by its lines and tells where is the attacker. True if not."""
        directions = [[0,1], [1,0], [0,-1], [-1,0]]
        for dr, dc in directions :
            row = ROW
            col = COL
            while (row+dr in range(8)) and (col+dc in range(8)):
                row += dr
                col += dc
                if BOARD[row][col] is not None :
                    break

            if BOARD[row][col] is None or BOARD[row][col].color == color: continue

            if BOARD[row][col].name in ["queen", "rook"] :
                return {"check":False, "square_attacker":(row,col)}
            elif (BOARD[row][col].name == "king") and (abs(row - ROW) <= 1 and abs(col - COL) <= 1) :
                return {"check":False, "square_attacker":(row,col)}
        return {"check":True, "square_attacker":(-1,-1)}
    

    def check_horses(BOARD, ROW, COL, color) :
        """Returns False if the square is threatened by a horse and tells where is the attacker. True if not."""
        horse_square = [[2,1], [2,-1], [-2,1], [-2,-1], [1,2], [-1,2], [1,-2], [-1,-2]]
        for dr, dc in horse_square:
            if (ROW+dr in range(8)) and (COL+dc in range(8)) and (BOARD[ROW+dr][COL+dc] is not None)\
            and BOARD[ROW+dr][COL+dc].name == "horse" and BOARD[ROW+dr][COL+dc].color != color:
                return {"check":False, "square_attacker":(ROW+dr,COL+dc)}
        return {"check":True, "square_attacker":(-1,-1)}
    



    ##################################################################################
    #### Functions to be used to see if one can block a check with a piece or not ####
    ##################################################################################

    
    def reach_sqr_from_lines(BOARD, ROW, COL, color) :
        """Checks if a Rook or Queen can reach the square(ROW, COL). Returns True if yes."""
        directions = [[0,1], [1,0], [0,-1], [-1,0]]
        for dr, dc in directions :
            row = ROW
            col = COL
            while (row+dr in range(8)) and (col+dc in range(8)):
                row += dr
                col += dc
                if BOARD[row][col] is not None :
                    break

            if BOARD[row][col] is None or BOARD[row][col].color != color: continue

            if BOARD[row][col].name in ["queen", "rook"] :
                return True
        return False
    
    
    def reach_sqr_from_diags(BOARD, ROW, COL, color) :
        """Checks if a Bishop or Queen can reach the square(ROW, COL). Returns True if yes."""
        m = MoveUtility.DIRECTION[color]
        directions = [[1,1], [1,-1], [-1,-1], [-1,1]]
        for dr, dc in directions :
            row = ROW
            col = COL
            while (row+dr in range(8)) and (col+dc in range(8)):
                row += dr
                col += dc
                if BOARD[row][col] is not None :
                    break
            
            if BOARD[row][col] is None or BOARD[row][col].color != color: continue

            if BOARD[row][col].name in ["queen", "bishop"]:
                return True
        return False


    def reach_sqr_with_pawn(BOARD, ROW, COL, color) :
        """checks if a pawn can reach the sqaure or not"""
        m = MoveUtility.DIRECTION[color]
        if ROW-m in range(8) and BOARD[ROW-m][COL] and BOARD[ROW-m][COL].name == "pawn"\
            and BOARD[ROW-m][COL].color == color :
            return True
        elif ROW-2*m == MoveUtility.first_rank[color] and BOARD[ROW-m][COL] is None\
            and BOARD[ROW-2*m][COL] and BOARD[ROW-2*m][COL].name == "pawn"\
            and BOARD[ROW-2*m][COL].color == color :
            return True
        return False


    def reach_sqr_with_horse(BOARD, ROW, COL, color):
        """Returns True if a horse of 'color' can reach the square."""
        horse_square = [[2,1], [2,-1], [-2,1], [-2,-1], [1,2], [-1,2], [1,-2], [-1,-2]]
        for dr, dc in horse_square:
            if (ROW+dr in range(8)) and (COL+dc in range(8)) and (BOARD[ROW+dr][COL+dc] is not None)\
            and BOARD[ROW+dr][COL+dc].name == "horse" and BOARD[ROW+dr][COL+dc].color == color:
                return True
        return False





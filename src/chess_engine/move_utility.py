"""Détection des cases attaquées, par rayons depuis la case examinée.

Plutôt que de demander à chaque pièce adverse si elle atteint la case, on part
de la case et on regarde ce qu'on rencontre : une seule marche par direction,
quel que soit le nombre de pièces sur l'échiquier.

Attention à la convention, héritée et contre-intuitive : ``check`` vaut
``False`` quand la case **est** attaquée. ``GamePosition.is_attacked`` inverse
la réponse, et c'est le seul appelant.
"""


class MoveUtility:
    DIRECTION = {"w": -1, "b": 1}

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
            # un pion n'attaque qu'en diagonale avant, donc à une case et dans son sens
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


    def check_knights(BOARD, ROW, COL, color) :
        """Returns False if the square is threatened by a knight and tells where is the attacker. True if not."""
        knight_squares = [[2,1], [2,-1], [-2,1], [-2,-1], [1,2], [-1,2], [1,-2], [-1,-2]]
        for dr, dc in knight_squares:
            if (ROW+dr in range(8)) and (COL+dc in range(8)) and (BOARD[ROW+dr][COL+dc] is not None)\
            and BOARD[ROW+dr][COL+dc].name == "knight" and BOARD[ROW+dr][COL+dc].color != color:
                return {"check":False, "square_attacker":(ROW+dr,COL+dc)}
        return {"check":True, "square_attacker":(-1,-1)}

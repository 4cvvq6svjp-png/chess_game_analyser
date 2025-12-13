

class Player :
    COLOR = {"b":"Black", "w": "White"}


    def __init__(self, color) :
        self.color = color
    

    def tell_a_move(self) :
        move = input(f"{self.COLOR[self.color]} to play (ex: 'a1/a3') : ")
        return move
    
    def tell_a_piece(self):
        """function to be used when a pawn reaches the back rank and therefore needs
            to be changed"""
        p = input(f"Which piece you want your pawn to become ?")
        return p
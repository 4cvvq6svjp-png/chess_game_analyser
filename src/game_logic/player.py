

class Player :
    COLOR = {"b":"Black", "w": "White"}


    def __init__(self, color) :
        self.color = color
    

    def tell_a_move(self) :
        move = input(f"{self.COLOR[self.color]} to play (ex: 'a1a3') : ")
        return move
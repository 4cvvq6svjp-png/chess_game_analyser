

class Board :
    def __init__(self):
        # how move history will be stored
        self.play_stack = []
        self.taken_squared = self.init_taken_squared()
        # TODO - history of moves when going through the different 
        self.explored_history = {}

    
    def init_taken_squared() :
        pass
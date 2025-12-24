from chess_game import chess_game


from fastapi import FastAPI, HTTPException
from api_schemas import MoveRequest,GameState
from chess_game import chess_game


# app definition
app = FastAPI()


TheGame = chess_game()

@app.post("/start", response_model=GameState)
def launch_game():
    global TheGame
    TheGame = chess_game()
    
    return TheGame.exporter_etat()


@app.post("/play", response_model=GameState)
def play_move(coup: MoveRequest):
    global TheGame



    # check if it points to a Piece
    try:
        if not self._could_be_a_move(square_from, square_to) :
            print("Your starting square is empty")
            print("PLease try anoter input")
            continue
    except Exception:
        print("Not a valid Move")
        print("Please rewrite your move")

    moving_piece = board.chessboard[square_from[0]][square_from[1]]


    if moving_piece._is_valid_move(square_from, square_to, board) :
        copy_board = deepcopy(board)
        moving_piece._execute_move(copy_board, square_from, square_to)
        if copy_board.is_in_check(curr_player.color)["check"] :
            print("you must not stay or go into CHECK!")
            continue
        
        if board._isbackrank_PawnMove(square_from, square_to):
            while True:
                piece_name = curr_player.tell_a_piece()
                if piece_name in ["queen", "rook", "knight", "bishop"]:
                    new_piece = Board.create_piece_by_name(piece_name, curr_player.color)
                    break
            moving_piece._move_piece(board.chessboard, square_from, "remove")
            new_piece._move_piece(board.chessboard, square_to, "add")
        else:
            moving_piece._execute_move(board, square_from, square_to)
        self.turn += 1  
    else:
        print("you cannot play this move try another one.")

    # watch for checks and checkmate
    self.check = False
    ischeck = board.is_in_check(next_player.color)
    if ischeck["check"] :
        print("CHECK!!")
        self.check = True
        if board.is_it_checkmate(next_player.color, ischeck["square_attacker"], ischeck["double_check"]):
            self.game_is_live = False
            self.checkmate = True
            continue
    
    # watch for stalemate
    isstalemate = board._is_stalemate()
    if isstalemate:
        self.game_is_live = False
        self.stalemate = True
        continue

    # watch for pat
    if not self.check and self.turn > 18 and board._is_pat(next_player.color) :
        self.game_is_live = False
        self.pat = True



    if not TheGame.game_is_live:
        raise HTTPException(status_code=400, detail="The Game is ended. Start a new one to play.")

    try:

        TheGame.execute_move(coup.row, coup.col)
    except ValueError as e:

        raise HTTPException(status_code=400, detail=str(e))

    return TheGame.export_state()




# def main() :
#     jeu = chess_game("test")
#     jeu.launch_game()


# if __name__ == "__main__" :
#     main()
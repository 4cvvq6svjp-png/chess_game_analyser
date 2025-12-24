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
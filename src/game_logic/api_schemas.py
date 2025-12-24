from pydantic import BaseModel
from typing import List, Optional
from pieces import Piece

class MoveRequest(BaseModel):
    row: int
    col: int

class GameState(BaseModel):
    message: str
    player_turn: int
    game_live: bool
    board: List[List['Piece']] 
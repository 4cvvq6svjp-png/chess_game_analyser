"""L'API HTTP du moteur, installée avec l'extra ``[api]`` : ``pip install -e ".[api]"``.

Un paquet à part, et non un module de ``chess_engine`` : le moteur reste sans
dépendance, et ``import chess_engine`` ne doit jamais tirer FastAPI.
"""

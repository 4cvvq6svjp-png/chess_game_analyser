from chess_game import chess_game


def main() :
    jeu = chess_game()
    jeu.launch_game()


def coordinate( move) :
    start, end = move.strip().split('/')
    # we assume that both are of length 2, and return the coordinates as tuples
    return (8 - int(start[1]), ord(start[0]) - ord("a")) , (8 - int(end[1]), ord(end[0]) - ord("a"))





if __name__ == "__main__" :
    #print(coordinate("e2/e4"))
    main()
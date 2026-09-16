from .chess_game import chess_game


def main():
    jeu = chess_game("classic")
    jeu.launch_game()


if __name__ == "__main__":
    main()

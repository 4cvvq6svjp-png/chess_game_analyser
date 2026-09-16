"""L'affichage terminal : une lettre par pièce, et six lettres distinctes.

Régression : tant que le cavalier s'appelait "horse", afficher son initiale
suffisait. Renommé en "knight", il est entré en collision avec "king" -- les
deux devenaient K. La notation algébrique règle ce conflit depuis toujours en
donnant N au cavalier.
"""

import io
import unittest
from contextlib import redirect_stdout

from helpers import Bishop, Board, King, Knight, Pawn, Queen, Rook, empty_board, place

KINDS = (Bishop, King, Knight, Pawn, Queen, Rook)


def rendered(board):
    output = io.StringIO()
    with redirect_stdout(output):
        board.display_board()
    return output.getvalue()


class TestLetters(unittest.TestCase):
    def test_every_piece_has_a_letter(self):
        for kind in KINDS:
            with self.subTest(piece=kind.__name__):
                self.assertIn(kind("w").name, Board.LETTERS)

    def test_the_six_letters_are_distinct(self):
        self.assertEqual(len(set(Board.LETTERS.values())), len(Board.LETTERS))

    def test_the_knight_is_n_and_the_king_is_k(self):
        self.assertEqual(Board.LETTERS["knight"], "N")
        self.assertEqual(Board.LETTERS["king"], "K")


class TestRendering(unittest.TestCase):
    def test_king_and_knight_are_told_apart(self):
        board = empty_board()
        place(board, King("w"), (7, 4))
        place(board, Knight("w"), (7, 6))
        text = rendered(board)
        self.assertIn("K", text)
        self.assertIn("N", text)

    def test_white_is_uppercase_and_black_lowercase(self):
        board = empty_board()
        place(board, Queen("w"), (0, 0))
        place(board, Queen("b"), (7, 7))
        text = rendered(board)
        self.assertIn("Q", text)
        self.assertIn("q", text)

    def test_a_full_back_rank_shows_every_piece(self):
        board = Board("classic")
        text = rendered(board)
        for letter in Board.LETTERS.values():
            with self.subTest(letter=letter):
                self.assertIn(letter, text)
                self.assertIn(letter.lower(), text)


if __name__ == "__main__":
    unittest.main()

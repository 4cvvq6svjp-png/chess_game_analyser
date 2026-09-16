"""Le contrat commun aux six pièces.

``GamePosition.legal_moves()`` parcourra l'échiquier et demandera ses coups à
chaque pièce sans savoir laquelle elle tient. Ces tests vérifient que cet
appel polymorphe fonctionne pour les six, et que le contrat est tenu par la
classe de base plutôt que par la discipline.
"""

import unittest

from helpers import (
    Bishop,
    GamePosition,
    King,
    Knight,
    Move,
    Pawn,
    Piece,
    Queen,
    Rook,
    empty_board,
    place,
)

CENTRE = (4, 4)
ALL_PIECES = (Bishop, King, Knight, Pawn, Queen, Rook)


class TestEveryPieceGenerates(unittest.TestCase):
    def test_each_kind_yields_moves_anchored_on_its_square(self):
        for kind in ALL_PIECES:
            with self.subTest(piece=kind.__name__):
                board = empty_board()
                piece = place(board, kind("w"), CENTRE)
                position = GamePosition.from_board(board)

                moves = list(piece.pseudo_moves(position, CENTRE))
                self.assertTrue(moves, f"{kind.__name__} ne produit aucun coup")
                self.assertTrue(all(isinstance(m, Move) for m in moves))
                self.assertTrue(all(m.square_from == CENTRE for m in moves))

    def test_no_move_ever_leaves_the_board(self):
        for kind in ALL_PIECES:
            for origin in [(0, 0), (0, 7), (7, 0), (7, 7), (3, 3)]:
                with self.subTest(piece=kind.__name__, origin=origin):
                    board = empty_board()
                    piece = place(board, kind("b"), origin)
                    position = GamePosition.from_board(board)
                    for move in piece.pseudo_moves(position, origin):
                        row, col = move.square_to
                        self.assertTrue(0 <= row < 8 and 0 <= col < 8)

    def test_no_piece_ever_stands_still(self):
        for kind in ALL_PIECES:
            with self.subTest(piece=kind.__name__):
                board = empty_board()
                piece = place(board, kind("w"), CENTRE)
                position = GamePosition.from_board(board)
                destinations = {m.square_to for m in piece.pseudo_moves(position, CENTRE)}
                self.assertNotIn(CENTRE, destinations)

    def test_a_piece_never_lands_on_a_friend(self):
        """Un échiquier saturé d'amis : plus aucun coup, pour aucune pièce."""
        for kind in ALL_PIECES:
            with self.subTest(piece=kind.__name__):
                board = empty_board()
                for row in range(8):
                    for col in range(8):
                        place(board, Pawn("w"), (row, col))
                piece = place(board, kind("w"), CENTRE)
                position = GamePosition.from_board(board)
                self.assertEqual(list(piece.pseudo_moves(position, CENTRE)), [])

    def test_the_call_is_polymorphic(self):
        """Le site d'appel ne connaît que Piece."""
        board = empty_board()
        pieces = [
            place(board, Knight("w"), (7, 1)),
            place(board, Rook("w"), (7, 0)),
            place(board, Pawn("w"), (6, 3)),
        ]
        position = GamePosition.from_board(board)

        generated = []
        for piece, square in zip(pieces, [(7, 1), (7, 0), (6, 3)]):
            self.assertIsInstance(piece, Piece)
            generated.extend(piece.pseudo_moves(position, square))

        self.assertTrue(generated)
        self.assertTrue(all(isinstance(m, Move) for m in generated))


class TestTheContractIsEnforced(unittest.TestCase):
    def test_a_piece_without_a_generator_cannot_exist(self):
        class Ghost(Piece):
            def _is_valid_move(self, square_from, square_to, BOARD):
                return False

            def _move_piece(self, board, square, add_or_remove):
                pass

            def _can_move(self, board, square):
                return False

        with self.assertRaises(TypeError):
            Ghost("w", "ghost")


if __name__ == "__main__":
    unittest.main()

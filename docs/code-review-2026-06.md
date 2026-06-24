# Code review — terminal chess engine (June 2026)

Review of the move/rules logic in `src/game_logic/`. The goal was to find
correctness bugs that let illegal moves through, declare false results, or
corrupt board state — and to add a regression test suite. Deferred features
(castling, insufficient-material draw, flag-fall, full threefold repetition)
were intentionally left untouched.

## Bugs fixed

| # | File | Problem | Fix |
|---|------|---------|-----|
| 1 | `knight.py` | `abs(col - colTO)` was missing `== 1`, so any move with a row-delta of 2 and *any* non-zero column delta validated as a knight move (e.g. `(0,0)→(2,5)`). | Require `abs(col - colTO) == 1`. |
| 2 | `move_utility.py` (`check_diags`, `check_lines`) | King-attacker test used `< 1`, i.e. distance 0, which is never true after the ray walk — so an enemy king never guarded a square and kings could move adjacent. | `<= 1`. |
| 3 | `king.py` | `King._is_valid_move` never checked the landing square's occupant, so a king could move onto and overwrite a friendly piece. | Reject a same-color destination. |
| 4 | `chess_board.py` (`is_it_checkmate`) | The king-escape scan only iterated the four diagonal squares, so a king whose only flight square was orthogonal was wrongly judged mated. | Iterate all 8 squares. |
| 5 | `pawn.py` | `Pawn._is_valid_move` removed the en-passant-captured pawn as a **side effect** of a validation call; the same method is called speculatively (check/stalemate scans), so it could delete a real pawn off the live board. | Made validation pure (`_is_en_passant` helper) and moved the capture into `Pawn._execute_move`. |
| 6 | `chess_game.py` | The `except` around `_could_be_a_move` printed an error but did not `continue`, falling through with a possibly-invalid square. | Added `continue`. |
| 7 | `move_utility.py` (`reach_sqr_with_pawn`) | The two-square-block branch read `BOARD[ROW-m][COL].color` (wrong square) and crashed with `AttributeError` when that square was empty; it also never checked the intermediate square. | Test the color on `ROW-2*m`, require an empty intermediate square. |
| 8 | `pawn.py` | The pawn double-step only checked the landing square, so a pawn could jump over a blocking piece. | Also require the intermediate square to be empty. |

### Incidental cleanups
- Removed an unused `import numpy as np` in `chess_board.py` that made the
  program fail to start unless numpy happened to be installed.
- Removed debug `print` statements (`"ici"`, `"bishop or queen"`,
  `"begin check for checkmate"`, the in-between-square dump, …) that spammed
  normal gameplay; kept the real game messages (`CHECK!!`, win/draw text,
  prompts).
- Moved the `is_it_checkmate` docstring above `BOARD = self.chessboard` so it is
  an actual docstring.

## Known limitations (NOT addressed — deeper work)
- **King-shadow on slider checks:** escape squares are tested with the king
  still on the board, so the king's own body can shield a square along the
  checking line (a king can appear to "slide" along the check). Fixing this
  needs the king removed from its square before evaluating escapes.
- **Capture/block legality:** mate detection treats the checking piece as
  capturable without verifying the capturer isn't pinned or that a king-capture
  target is undefended.
- `_is_stalemate` repetition (`play_stack[:4] == play_stack[4:]`) only matches at
  exactly 8 plies and isn't true threefold repetition.
- `_is_pat` / `_can_move` don't filter moves that leave the own king in check.

These are flagged in the README's running notes as future work.

## Tests
A dependency-free `unittest` suite lives in `tests/` (Python stdlib, no pytest).

Run it from the repo root:

```bash
python -m unittest discover -s tests -t tests -v
```

`tests/helpers.py` adds `src/game_logic` to `sys.path` and exposes an
`empty_board()` / `place()` builder so each test is a minimal, readable
position. Coverage: knight/king/slider/pawn move legality, en-passant purity and
execution, check detection for every attacker type (incl. adjacent king and
double check), checkmate vs. orthogonal-escape, stalemate (`_is_pat`), and
move parsing. Every fix above has at least one regression test.

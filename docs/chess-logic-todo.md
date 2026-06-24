# Chess logic — deferred work / known gaps

Things the rules engine still gets wrong or doesn't implement yet, with **why it
matters** and a **suggested approach**. Roughly ordered by correctness impact.
Companion to [`code-review-2026-06.md`](./code-review-2026-06.md), which covers
what was already fixed.

---

## 1. King "shadow" on sliding checks  (correctness — high)
**What:** when `is_it_checkmate` (and king move validation in general) tests
whether an escape square is safe, the king is still sitting on its current
square. Its own body blocks the line of a checking rook/bishop/queen, so a
square *behind* the king along the check line looks safe when it isn't.

**Why it matters:** the king can appear to "slide" one square away from a rook/
queen along the line of check, and `is_it_checkmate` can return *not mate* on a
real mate. This is the single biggest remaining correctness hole.

**Approach:** before evaluating escape squares, temporarily treat the king's
origin square as empty (remove the king, or evaluate on a copy with the king
lifted), then test each candidate square's safety. Restore afterwards. The
`deepcopy` pattern already used in `chess_game.launch_game` is the natural tool.

---

## 2. Capture / block legality — pins and defenders  (correctness — high)
**What:** mate detection decides the checking piece "can be eaten" purely by
asking whether any friendly piece *attacks* its square (`check_diags/lines/
horses`). It never checks that:
- the capturing piece isn't **pinned** (capturing would expose its own king), or
- when the **king** is the capturer, that the attacker is **undefended**.
The blocking logic (`reach_sqr_*`) has the same blind spot for pinned blockers.

**Why it matters:** false *not mate* — e.g. "the queen can take the checker" when
that queen is pinned, or "the king takes the checker" when it's defended.

**Approach:** instead of the attack-based shortcut, generate each candidate
capture/block, play it on a `deepcopy`, and keep it only if
`is_in_check(own_color)` is then False. This is the same validation
`launch_game` already does for the human's move — lift it into a shared helper
and reuse it everywhere a "legal move" is needed.

---

## 3. `_is_pat` / `_can_move` ignore self-check  (correctness — high)
**What:** `_can_move` counts a move as available as long as the piece *can
geometrically move there*. It never rejects moves that leave (or put) the side's
own king in check.

**Why it matters:** stalemate detection (`_is_pat`) over-counts legal moves, so
it can fail to detect a real stalemate; conversely the engine treats some
illegal moves as legal escapes. This and #2 share the same root cause.

**Approach:** make `_can_move` (or a new `legal_moves(color)` generator) filter
candidates through the deepcopy + `is_in_check` check from #2. Once that exists,
`_is_pat`, checkmate, and stalemate all become "no legal move exists".

---

## 4. Promotion is missing from the move history  (correctness — medium)
**What:** in `launch_game`, the promotion branch calls `_move_piece` directly
and does **not** append to `board.play_stack`; it also loops on
`tell_a_piece()` with no way out on bad input.

**Why it matters:** `play_stack` is the source of truth for en-passant detection
(and any future undo / repetition / PGN export). A promotion move silently
vanishes from history, which will break those features. The input loop can also
spin forever on EOF.

**Approach:** route promotion through `_execute_move` (or append an explicit
promotion record including the chosen piece), and validate the promotion input
with a re-prompt + sane default.

---

## 5. Threefold-repetition draw  (rule completeness — medium)
**What:** `_is_stalemate` uses `play_stack[:4] == play_stack[4:]`, which is only
ever true at exactly 8 plies and isn't repetition anyway.

**Why it matters:** it essentially never fires, and the name/intent (a draw rule)
isn't actually implemented.

**Approach:** hash the full *position* (piece placement **plus** side to move,
castling rights, and en-passant square — two positions are only "the same" if all
of those match) into a dict of counts; declare a draw on the 3rd occurrence.
A FEN-like string is a convenient key.

---

## 6. Castling  (rule completeness — medium)
**What:** not implemented.

**Why it matters:** a core rule; games can't be played/imported faithfully
without it.

**Approach:** track "has moved" flags for each king and rook (a boolean on the
piece, set in `_execute_move`). Allow castling only when: neither piece has
moved, the squares between are empty, the king is not currently in check, and
the king does not pass through or land on an attacked square (reuse the
square-attacked helpers).

---

## 7. Draw-by-insufficient-material & flag-fall  (rule completeness — low)
**What:** already noted in the README. K vs K, K+minor vs K, etc. should be
draws; and a flag-fall (clock to 0) is only a loss if the opponent has mating
material.

**Why it matters:** needed for a complete result set once a clock exists.

**Approach:** a material-count helper invoked at game end / on flag-fall.

---

## 8. Fifty-move rule  (rule completeness — low)
**What:** not tracked.

**Why it matters:** completeness; also interacts with the repetition/draw logic.

**Approach:** a halfmove counter reset on any pawn move or capture, draw at 100
halfmoves.

---

## Assumptions worth revisiting
- **`is_in_check` double-check accounting** assumes at most one attacker per
  category (diag / line / horse). Two simultaneous checks from the *same*
  category are geometrically impossible in a legal position, so this holds — but
  it's an implicit invariant; document or assert it if the move generator is
  ever fed arbitrary positions (e.g. imported games / puzzles).
- The `check_*` / `reach_sqr_*` helpers are duplicated four ways (diag, line,
  pawn, horse) with near-identical ray-walking. Once #2/#3 introduce a real
  move generator, much of this can collapse into it.

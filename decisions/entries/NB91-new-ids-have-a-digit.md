# NB91 — New IDs have a digit and a letter

**Status:** accepted, 2026-10-29 (user; PR: pending).

## Decision

1. **The rule for a new ID.** A new ID has 4 characters from `ALPHABET`, Crockford base32 in upper
   case: `0123456789ABCDEFGHJKMNPQRSTVWXYZ`. It has at least one digit and at least one letter. The
   digit and the letter can be in any position, for example `3K7Q`, `K7M2` or `9A9A`. It does not
   have the form of a number in scientific notation, for example `1E23` or `12E3`.
2. **The draw.** `uv run python tools/check_decision_log.py --new` gives each valid new ID the same
   probability. It draws 4 characters from `ALPHABET`. It draws again when the 4 characters are all
   digits or all letters, or have the form of a number. Then it skips an ID that is already in use, as before.
3. **Old IDs.** Each old ID stays valid. An all-digit ID belongs only to an old numbered entry, 0001
   to 0048. An older ID in lower case starts with a letter. The checker accepts an upper-case ID with
   a digit first in a file name, an index row, a link and a status line.
4. **The source.** The docstring of
   [`tools/check_decision_log.py`](../../tools/check_decision_log.py) states this rule and cites
   this entry. [ADR-Z05A](Z05A-essential-decision-log-rules.md) made the tool docstrings the source
   of the rules that they check. This entry changes the ID rule in that docstring. It does not change
   a rule of that entry, so it does not supersede that entry. The kit gets the rule by
   [`tools/sync_bootstrap_kit.py`](../../tools/sync_bootstrap_kit.py), and the kit guide
   [`specs/agents-and-adr-process/README.md`](../../specs/agents-and-adr-process/README.md) states it.

## Reason

- The user decided on 2026-10-29. An ID with only letters can read as a word for a person or for a
  grep, for example `FADS`. A digit in each new ID stops this.
- A letter first is not necessary when each new ID has a digit and a letter. A digit first gives
  more IDs:

  | Rule | Valid new IDs |
  |---|---|
  | A letter first ([ADR-GTWQ](gtwq-random-entry-ids.md)) | 22 × 32³ = 720,896 |
  | A letter first and a digit | 22 × (32³ − 22³) = 486,640 |
  | A digit and a letter in any position, not a number (this entry) | 32⁴ − 10⁴ − 22⁴ − 2,000 = 802,320 |

- More IDs make a collision between parallel branches less frequent.
- A redraw is simple, and it keeps the draw uniform. Each string of 4 characters has the same
  probability, so each valid ID also has the same probability after the redraw. About 23% of the
  draws are all digits or all letters, so the redraw costs almost nothing.

## Consequences

- About 39.5% of the new IDs start with a digit. In a file listing, such an ID can sort between two
  old numbers, for example `001A` between `0019` and `0020`.
- YAML 1.2 and spreadsheets read an ID of the form `1E23` or `12E3` as a number. The draw excludes
  these 2,000 IDs. Still write an ID in YAML in quotes.

## Alternatives rejected

- **A letter first and a digit in the last 3 characters.** It gives 486,640 IDs, about 40% fewer than
  this rule, and the user did not want the restriction.
- **A fixed position for the digit.** It gives fewer IDs and adds a pattern with no use.

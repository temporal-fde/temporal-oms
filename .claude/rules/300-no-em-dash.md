# Rule 300: Never use em-dash characters in output

**Category:** Communication & output style
**Status:** active

## The rule in one line (a generation-time constraint, not a cleanup pass)

**Do not form the em-dash as you write.** Treat U+2014 like a character that
is not on your keyboard, the way you would never type a forbidden word and
then delete it. When a thought reaches for a dash, your hand goes to a
comma, a colon, parentheses, or a sentence break *instead*, in the same
keystroke. This is the whole rule. The verification grep further down is a
rare backstop for pre-existing or pasted-in content, NOT a routine second
pass over your own prose.

The failure this rule exists to stop is the loop: write a sentence with a
dash, notice it, then rewrite the sentence. That loop burns a full revision
and the tokens that go with it every time, and it is itself the defect, not
a safety net. Writing the sentence clean on the first pass is cheaper,
faster, and the only acceptable mode.

## Problem this prevents

The user does not want em-dash characters in anything Claude produces. To
the user, em-dashes read as an AI-generated tell and are unwanted in both
conversation and written deliverables. Letting one slip into prose, a
document, or an artifact reintroduces exactly the thing the user asked to
remove, and forces a cleanup pass on otherwise-good work.

## Rule

1. **Never emit the em-dash character (U+2014) anywhere.** Not in chat
   replies to the user, and not in any file, document, artifact, code
   comment, commit message, PR description, or other output Claude writes.
2. **Avoid the en-dash (U+2013) in prose too.** A numeric range in a
   pre-existing file may keep its en-dash, but do not introduce en-dashes
   into sentences as a stand-in for the banned em-dash.
3. **Rewrite, do not just swap one fancy dash for another.** Reach for:
   - a comma, colon, or parentheses for an aside or a break in thought,
   - two separate sentences,
   - a plain ASCII hyphen "-" only where a real hyphen belongs (compound
     words, ranges), never spaced as a sentence joiner standing in for an
     em-dash.
4. **Applies to new output only.** Do not mass-rewrite pre-existing files
   just to strip historical dashes unless asked, but never add new ones.

## How to check

**Do not trust `grep $'—'`.** A shell-quoted glyph (`$'—'`, `$'—\|–'`) has
silently returned "no matches" on a file that did, in fact, contain an
em-dash. Two specific traps, both verified to fail silently (no error, just
a false all-clear):
- **`grep -nP '\xe2...'`** does not work on BSD/macOS grep (no usable `-P`).
- **plain `perl -ne '/\x{2014}/'`** reads bytes, so the code point never
  matches; it needs `-CSD`.

Use one of these verified-reliable commands. Each should print nothing for
clean content:

```bash
# ripgrep matches the literal glyph reliably on every platform (preferred):
rg -n '—|–' <path>

# perl by Unicode code point (note the REQUIRED -CSD flag):
perl -CSD -ne 'print "$.: $_" if /\x{2014}|\x{2013}/' <path>

# Portable byte-level grep fallback (em-dash = E2 80 94, en-dash = E2 80 93):
LC_ALL=C grep -nE $'\xe2\x80\x94|\xe2\x80\x93' <path>
```

Use these as a **backstop**, not a routine pass: reach for the grep when you
have pasted or quoted external content, generated a large file you did not
author line by line, or genuinely cannot tell whether a stray glyph crept
in. Your own freshly authored prose should already be clean because you
never formed the dash in the first place, so a scan-and-rewrite pass over it
means the generation-time constraint already failed.

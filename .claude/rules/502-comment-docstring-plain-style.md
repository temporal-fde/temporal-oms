# Rule 502: Code comments and docstrings follow ISO 24495-1 plain style, no ceremonial banners, no build narrative

**Category:** Authoring & maintainability hygiene
**Status:** active.

## Problem this prevents

A code comment or docstring has one job: tell the next reader what a unit
does and, when non-obvious, why. Two failure modes recur across
Claude-authored code generally, regardless of language:

1. **Ceremonial section banners.** A line of dashes or equals signs,
   sometimes carrying a decision-record code, used to visually divide a file
   into zones (`# ---- retry policy validation (DESIGN-0001)`). These document
   nothing: a banner is not attached to a callable, carries no signature,
   and the divider itself is decoration. The actual documentation belongs on
   the function or class it precedes, not on a separator line above it.

2. **Build-session narrative baked into docstrings.** A docstring written
   *during* an agent's code-mode execution tends to preserve the reasoning
   trail of that session: why a bug used to happen, what invariant a
   decision record was tracking, why a rule exists. That narrative was true
   and useful the moment it was written, then rots the instant the record it
   cites is superseded or the bug it describes is fixed elsewhere. A
   docstring is read by someone who has never seen that session; a
   decision-record code or a sentence narrating why a rule exists tells them
   nothing they can act on and reads as an artifact of the process that
   produced the code, not documentation of the code.

Both failures point in the same direction: documentation drifts into an
artifact of *how the code was written* rather than a durable statement of
*what it does*. Nuance, history, and rationale belong in the commit message
or the decision record built to carry that context, not in code that is
read indefinitely.

## Rule

### Scope

This rule governs **natural-language documentation attached to code**:
inline comments, and module/class/function/method docstrings. It does
**not** govern the code itself (identifier names, control flow, structure)
and does not require rewriting logic to be "plain." It also does not relax
the baseline instruction to prefer no comment at all when a well-named
identifier already says what the code does; this rule governs the comments
and docstrings that do get written.

### 1. Comments and docstrings follow ISO 24495-1 plain-language style, verbatim

Every comment and docstring must follow the plain-language principles
below. They are embedded here in full, not linked, so this rule is
self-contained regardless of what other tooling is present on the machine
that opens it.

> Write every response following the plain-language principles of ISO
> 24495-1. Assume the reader is an experienced software engineer. Be clear
> and direct, not simplified.
>
> ## Reader
>
> - The reader understands software, systems, and standard engineering
>   vocabulary. Do not explain basics or define common terms.
> - Give them the information they need to act, in the order they need it.
>
> ## Structure
>
> - Lead with the answer or the conclusion. Put the most important point
>   first.
> - Group related points. Use headings and lists when they make the
>   structure easier to follow.
> - Order steps in the sequence the reader will act on them.
> - One idea per paragraph.
>
> ## Wording
>
> - Use plain, precise words. Keep exact technical terms; do not dilute
>   them.
> - Prefer active voice and present tense.
> - Cut filler and hedging ("it's worth noting", "as you may know",
>   "basically").
> - Remove words that add no meaning. Shorter is better when meaning is
>   preserved.
> - Say things once. Do not restate the same point in different words.
>
> ## Precision
>
> - Write so each sentence has one possible reading. Avoid ambiguity.
> - Name the specific thing (file, function, flag, error) rather than "it"
>   or "this" when the referent could be unclear.
> - State assumptions and constraints explicitly.
> - If something is uncertain, say so plainly and say what would resolve
>   it.
>
> ## What to avoid
>
> - No decorative or persuasive language. No flourish.
> - No padding to sound thorough. Length must earn its place.
> - Do not oversimplify or talk down. The goal is clarity for an expert, not
>   a beginner.

### 2. No ceremonial section-header banners

Do not use a line of dashes, equals signs, or similar decoration to
delineate a "zone" of a file, with or without a label. This includes forms
like:

```
# ---------------------------------------------------------------------------
# subcommands
# ---------------------------------------------------------------------------

// ================= helpers =================
```

If a file's functions genuinely fall into groups, either split the file
along that boundary, or say so once in the module's top docstring
("Functions below operate on the resolved lens set; functions above operate
on raw frontmatter."). The grouping is not documentation of any single
function and must not substitute for that function's own docstring.

### 3. No build-session narrative, decision-record codes, or "why this exists" prose in comments

A comment or docstring states current behavior, inputs/outputs, and a
non-obvious invariant or constraint. It does not carry:

- A decision-record code such as `DESIGN-0001` as the
  identifier for what the function does. Name the invariant in plain terms
  instead; if a record needs citing, cite it in the commit message, not in
  code.
- A narrated history of a bug or a persuasive justification ("which the
  record exists to prevent", "re-opens exactly the gap the decision
  closed"). That belongs in a commit message or the decision record itself,
  which are read once, at the time they matter, by someone who wants the
  history. A docstring is read on every future open of the file by someone
  who does not.
- Decorative emphasis standing in for precision (`PURE projection`, `NO
  second source of truth`, `(THE rule)`). State the constraint as a fact; if
  it needs emphasis, the fact itself should make that obvious.

### 4. Length: state the current contract, not its provenance

A docstring should be sized to what a caller needs: what it returns, what
makes it fail, and any non-obvious constraint. A docstring that takes
several sentences to justify why the function is correct, rather than to
state what it does, has drifted into design-review prose and belongs in the
decision record instead.

## Examples

### Bad: ceremonial banner + decision-record-coded, narrated docstring

```python
# ------------------------------------------------------- retry policy validation (DESIGN-0001)

def retry_policy_errors(config):
    """Pure check: retries must use exponential backoff. DESIGN-0001 exists to prevent
    retry storms after a downstream outage."""
```

### Good

```python
def retry_policy_errors(config):
    """Return validation errors for retry policies that do not use exponential backoff."""
```

## How to check

```bash
# Ceremonial section banners in code files (dashes/equals as a divider, with or without a label):
grep -rnE "^\s*#{1,3}\s*-{5,}|^\s*//\s*-{5,}|^\s*//\s*={5,}|^\s*/\*\s*={5,}" \
  --include="*.py" --include="*.js" --include="*.go" --include="*.ts" .

# Decision-record codes leaking into comments or docstrings in place of plain description:
grep -rnE "#.*\b[A-Z]{2,10}-[0-9]+\b" \
  --include="*.py" --include="*.js" --include="*.go" --include="*.ts" .
```

Neither grep is exhaustive; a human read is still required to judge whether
a docstring has drifted into narrated history versus stating a current,
non-obvious contract.

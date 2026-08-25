# Rule 500: Reference a Skill Workflow step by its name, never its ordinal number

**Category:** Authoring & maintainability hygiene
**Status:** active

## Problem this prevents

Skills can describe their process as a numbered `## Workflow` list whose
items open with a bold name, for example:

```text
1. **Intake.** Treat the contributor's initial input ...
2. **References.** Ask the contributor whether they have any References ...
3. **Title and id.** ...
```

The number is positional: inserting, splitting, reordering, or merging a
Workflow item shifts every later number. Anything that cites a step by its
ordinal ("see step 2", "after step 4", "step 3, second bullet") silently
points at the wrong place the next time the list changes, and nothing fails
loudly to catch it.

## Rule

1. **Never reference a Skill Workflow step by its ordinal number**, from any
   file: the `SKILL.md` itself, a `references/*.md`, a spec, a decision
   record, or prose.
2. **Reference a step only by its bold name label** (the words inside the
   leading `**...**`), set off as a name: "the References step", "during
   Intake". A paraphrase or role nickname doesn't count as the name; cite
   the label verbatim.
3. **Applies to new and updated content.** When drafting or editing any
   file, don't introduce an ordinal reference to a Workflow step; when a
   line already carries one, convert it to the step's name in the same edit.

## Example

Flagged:

> Confirm the wording before step 3.

Correct:

> Confirm the wording before the *Title and id* step.

## How to check

```bash
# Numeric step references to review (a genuine unrelated ordinal is a false positive):
grep -rnE '\b(step|item) [0-9]+\b' skills/ specs/ --include="*.md" -i
```

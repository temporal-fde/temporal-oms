# `.claude/rules/`

Numbered, single-topic behavioral rules for how Claude should operate in
this repository. These are tooling and behavior conventions: how to use Bash,
how to edit files, how to write output, and how to keep authored text
maintainable. They are distinct from the repository-specific guidance in
[`AGENTS.md`](../../AGENTS.md), the application documentation under
[`docs/`](../../docs/), and feature specifications under [`specs/`](../../specs/).

Each rule is one file: `NNN-short-slug.md`. The **hundreds digit is the
category**:

| Range | Category |
|---|---|
| 100-199 | Shell / tooling hygiene |
| 200-299 | _(unclaimed)_ |
| 300-399 | Communication & output style |
| 400-499 | _(unclaimed)_ |
| 500-599 | Authoring & maintainability hygiene |

Add a new category by claiming the next free hundreds block and recording it
in this table.

## Active rules

Skim this index first; open the linked source file only when a rule
applies. Keep it in sync: every rule added/renamed/removed updates this
list in the same edit.

1. **Rule 100: [Use absolute paths in Bash; never prepend `cd`](100-shell-absolute-paths-no-cd.md)**
   Always pass absolute paths to Bash commands and never open a command with `cd X && …`, because the Bash tool already persists its working directory between calls. A leading `cd` adds nothing and triggers a permission prompt the sandbox can reject.

2. **Rule 101: [Create and edit files with the Write/Edit tools, never bash heredoc or shell redirection](101-file-edits-via-tools-not-heredoc.md)**
   Write or modify repository files only through the Write and Edit tools, never with a `cat <<'EOF' > file` heredoc, `echo`/`printf` redirection, `sed -i`, `tee`, or `>>` appends. The dedicated tools render every change as a reviewable diff the user can follow live; a shell heredoc buries the file content inside an opaque Bash call the user cannot review.

3. **Rule 300: [Never use em-dash characters in output](300-no-em-dash.md)**
   Never emit the em-dash character (U+2014) in any output: not in conversation, and not in any file, document, artifact, code comment, or commit message. Avoid en-dashes in prose too. Rewrite with commas, colons, parentheses, or separate sentences instead of swapping in another dash. Applies to new output; do not add new ones.

4. **Rule 301: [Use terse, pragmatic communication](301-terse-pragmatic-communication.md)**
   Use the terse, pragmatic personality for work in this repository. Match Claude's concise style: direct, technical, and low ceremony. Lead with the result, decision, risk, or next action.

5. **Rule 500: [Reference a Skill Workflow step by its name, never its ordinal number](500-no-workflow-step-number-references.md)**
   Skills can describe their process as a numbered `## Workflow` list whose items open with a bold name, such as `1. **Intake.**`. The number is positional and shifts when items are inserted, split, or reordered, so any file that cites "step 2" silently breaks on a reorder. Reference a step only by its bold-label name, set off as a name, such as "the References step".

6. **Rule 502: [Code comments and docstrings follow ISO 24495-1 plain style, no ceremonial banners, no build narrative](502-comment-docstring-plain-style.md)**
   Inline comments and docstrings must follow the ISO 24495-1 plain-language principles verbatim, must never use a ceremonial dashes/equals section banner to divide a file into zones, and must never carry build-session narrative or decision-record codes in place of a plain statement of current behavior.

# Rule 100: Use absolute paths in Bash; never prepend `cd`

**Category:** Shell / tooling hygiene
**Status:** active

## Problem this prevents

A command shaped like `cd /some/abs/path && <command>` triggers a permission
prompt and can be rejected by the sandbox. The Bash tool already **persists
its working directory between calls**, so the `cd` adds nothing and costs a
round-trip (or an outright denial).

## Rule

1. **Pass absolute paths to the command itself.** Do not change directory to
   reach a file.
2. **Never chain `cd X && …`** in a single Bash invocation.
3. If many calls genuinely operate in the same directory, rely on the
   persisted cwd from a prior plain call; still do not open a command with
   `cd`.

## Example

Flagged (prompts / can be denied):

```bash
cd /Users/x/dev/project/docs && grep -l "Accepted" *.md
```

Correct (absolute path, no `cd`):

```bash
grep -l "Accepted" /Users/x/dev/project/docs/*.md
```

## If a `cd`-based pattern is truly unavoidable

Prefer rewriting to absolute paths. Only as a last resort, add an explicit
allow entry for the specific command in `.claude/settings.local.json`
(`permissions.allow`); the absolute-path rewrite is the intended fix,
not a broad `cd` allowance.

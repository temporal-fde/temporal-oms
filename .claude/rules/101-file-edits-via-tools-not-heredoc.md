# Rule 101: Create and edit files with the Write/Edit tools, never bash heredoc or shell redirection

**Category:** Shell / tooling hygiene
**Status:** active

## Problem this prevents

When a file is created or modified through a Bash command (a `cat <<'EOF' >
file` heredoc, an `echo`/`printf` redirection, `sed -i`, `tee`, or any
`>`/`>>` redirection), the change is buried inside an opaque Bash tool call.
The user watching the session sees a shell invocation, not the file's
contents, and cannot follow, review, or catch a mistake as it happens. The
Write and Edit tools exist precisely so every file change surfaces as a
reviewable diff in the transcript.

## Rule

1. **Create a new file with the Write tool.** Do not create files with
   `cat <<'EOF' > file`, `echo ... > file`, `printf ... > file`, `tee file`,
   or any other shell redirection.
2. **Modify an existing file with the Edit tool** (or the Write tool for a
   full rewrite of a file already read). Do not modify files with `sed -i`,
   `perl -i`, `awk ... > tmp && mv`, `>>` appends, or redirection.
3. **Applies to every file worth reviewing**, including throwaway scratch
   scripts and generated config. Using the tool costs nothing; a hidden edit
   costs the user the audit trail and the chance to catch an error as it
   happens.
4. **The narrow exception is a genuine non-file shell effect**: piping data
   between commands, redirecting a command's stdout into a scratch capture
   read back by the agent itself, or a tool that only writes files as a
   documented side effect (a formatter, a compiler, `git`). Producing file
   *content* that belongs in the repo, or that the user should review,
   always goes through Write or Edit.

## Example

Flagged (buries the file content inside a Bash call the user cannot review):

```bash
cat > script.py <<'EOF'
print("hello")
EOF
```

Correct: call the Write tool with `file_path` set to the target and the file
content as `content`. The change then renders as a diff in the transcript.

## How to check

```bash
# Shell file-writing patterns that should have gone through Write/Edit (review each hit):
grep -nE "<<'?EOF|(^|[^0-9>])>[^>&]|>>|sed -i|perl -i| tee " <script-or-transcript>
```

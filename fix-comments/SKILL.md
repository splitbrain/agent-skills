---
name: fix-comments
description: Review the project's inline comments and doc blocks against the comment rules, and fix what violates them. Use when asked to check, clean up or update comments or docblocks, or before committing a finished change.
---

# Comment review

Applies to any language. Read the \writing-rules skill. Apply it to the scope.

## Scope

The scope varies depending on how the user called the skill:

* `fix-comments` with out any additional info scopes to the current changes only. Only edit doc blocks
  or inline comments on currently modified, uncommitted code
* `fix-comments branch` means to adjust all code that has been changed in the current branch compared against
  it's base branch. If there is an remote origin of this branch, ask before touching any code that has been pushed
  already
* `fix-comments <scope>` the user may give instructions on the scope. Either in plain text or as commit ID or similar
  reference.

Once you decided what the scope probably is, get confirmation from the user before changing any files!

ALWAYS get scope confirmation! NEVER start without explicit confirmation!


## Procedure

1. List the changed files and read each one fully.
2. Per comment: is it adhering to the /writing-rules, and is every claim true?
3. Change comments only. Missing type annotations, misplaced classes and other code faults are reported,
   not fixed, unless the user asks.
4. Re-run whatever the project uses to check the files still parse — linter, formatter, type checker,
   build. Respect the project's line length.
5. Report grouped by pattern, saying what was cut and why — plus, separately, any claim that proved false
   and any code issue left for the user to decide.

## Anti-pattern

Searching for markup and missing tags is not this review. Every comment has to be read and judged
against the code it sits on: a file can satisfy every language rule and still be full of comments
that argue, restate or lie, and reporting it as compliant is the wrong answer.

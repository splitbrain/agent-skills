---
name: writing-rules
description: Rules to adhere to for any technical writing, may it be documentation, inline comments, git commits or PR
  descriptions
---

# General Technical Writing

Keep the language simple! You're not here to win an essay contest. You need to convey important information.
Adhere to the KISS-principle: keep it simple stupid.

## Rules

- **Simple and short.** If you can say it simpler and shorter, do it. One sentence is better than three.
- **Standalone Docs.** Documentation needs to stand on it's own. Do not reference chat sessions, plans or other
  ephemeral files.
- **Prefer prose.** Use bullet lists only when you are actually listing things. Otherwise prefer proper prose

If the `plain-writing` skill is available, read it first, then apply what is described here on top.

## Anti-Patterns

Never use these. Cut on sight.

- **Counterfactuals.** Documentation should be about what *is*, not what was or could have been. Say what you want to
  say, not what has been discussed but rejected. The reader is looking at what exists.
- **Duplication.** Do not repeat yourself. Say what needs to be said once at one place. Refer to that place when the
  same information is usefule elsewhere
- **Inventing Words.** Do not make up words. Use the established vocabulary of the project. If there is a glossary, use
  it!
- **Antropomorphizing.** Code and other inanimate objects do not "own", "think", "say" or "carry" anything. Be
  precise and say what you actually want to express without metaphors.
- **Question words for non-questions.** Never start statements or headlines with "what", "whether", "why" etc.

## Language

Follow these general language guidelines.

- **Subject, verb, object.** No inversions, no correlatives ("neither X nor Y is…"), no clefts ("what this does
  is…", "the value it hands back is…").
- **Plain verbs.** "the plugin cannot change them", not "they are not the plugin's to change". No possessive
  infinitives, no nominalised verbs ("performs a validation of"), no auxiliary pile-ups.
- **Name the actor.** Prefer the active voice. Name the actor.
- **No intensifiers or hedges.** "only ever", "simply", "actually", "of course", "note that". They carry emphasis,
  never information.
- **Concrete verbs, not vague pairs.** "asks and reports" says nothing. "Sends the request and shows the status" says
  it.
- **One fact per sentence.** Three facts chained with "and … so … which" are three sentences.

## Updates

When updating existing documentation, change it to include the new facts. Do not simply add the new facts as new
sentences or praragraphs. Do not be afraid of rewriting existing documentation when needed.

Do not add "Answered Questions" or "Decisions" sections. Rework the document to incorporate the new facts.

When existing documentation consists of multiple documents, think hard to which document a new fact belongs. Do not
repeat yourself across multiple documents!

# Plans

When planning new features you will often be asked to write a detailed implementation plan first.

Where existing features are changed, the plan should make clear how the feature currently works and how the new
implementation will change it and what the goals are. This is the one place where historical contrast is wanted!

Be sure that used time forms always reflect what describes current state (present tense) and planned state
(future tense).

Apply the rules on Updates as outlined above, when extending a plan.


# Code Documentation

While the above general rules always apply, you need to pay additional attention when adding documentation to the
source code itself.

The most important rule is: do not repeat what the code already says!

## Additional issues to avoid

- **Platform tutorials.** How the framework, standard library or runtime works. Assume the reader knows the platform.
  Keep only the one specific quirk without which this code looks wrong.
- **Counterfactuals.** Already mentioned above. It's especially important for code documentaion. Only ever describe
  the actual code. Not what was there before or what alternatives were rejected.
- **Design justification.** "Written once so the checks cannot drift apart." "Public because both are the same
  question." Say what it does. One clause is the limit, and only where the design is genuinely surprising.
- **Duplication.** A fact belongs on the element that owns it. If a class header explains what one method writes, cut
  it from the header, not from the method.
- **Restatement.** Saying what the code says. In tests this appears as narration repeating the test name or its own doc
  comment.
- **Historical contrast.** "instead of at the first call", "no longer waits for", "previously". Describe the behaviour
  that exists; the diff carries the change.
- **Negatives.** Never explain what code does not. Or things that happen elsewhere but not in the code being described
  right now.
- **Pronouns** "we" and "you" do not belong in comments
- **Inventories.** A class or file header enumerating what its own members do — the steps it runs, the columns it
  renders, the shape of its output, the pieces it is assembled from. Each fact belongs on the member that owns it,
  where it cannot drift. Distributed across a paragraph this never trips the duplication rule, so check the header as
  a whole.
- **Dependency Lists.** The dependencies and which version of them are used is managed by the appropriate package
  management files. Comments referencing dependencies are bound to go stale soon.

## Doc blocks

A doc block is whatever the language uses for documented API elements — docblock, docstring, JSDoc, KDoc, rustdoc,
XML doc comment. Follow best practices for formatting. Use the full line length - typically 120 chars. Be sure to
stay consistent with the existing formatting.

Every class, method, function, constant and field should have a doc block. It contains a summary, an optional body and
the parameter and return value descriptions.

The summary line says what the thing is or does. Body paragraphs, if any, explain behaviour that is not obvious. A doc
block should rarely have more than three lines beyond its summary.

A doc block must stand on its own: no "see the docs", no pointer to another file or a ticket, no reliance on the
comment above it. Spec and RFC names are facts about behaviour and may stay.

Avoid using markup (like markdown or HTML) in the doc block.

## Inline comments

An inline comment is a documentation comment inside a class or method body (typically using `//`, `#` or `/* */`).

Minimal, and only where they structure or explain. Two legitimate jobs:

- **Structure** - a short label marking a step in a long sequential procedure
- **Explain** - the reason behind code whose shape is otherwise surprising: an ordering constraint, a security
  consequence, a workaround for a platform quirk, a deliberate omission that looks like a bug

Rules:

- Never restate the next line. `// close session` above a call that closes the session is pure noise.
- Sit directly above, or at the end of, the code the comment is about. A comment must not float in a file or at the top
  of a body describing something further down.
- One line by default. Three is a lot. If the reasoning needs more, it belongs in the doc comment of the enclosing
  function, or the code needs better names.
- A comment explaining what the code does *not* do is suspect. Keep it only as a guard against a plausible future
  mistake, in one line.
- No commented-out code. Delete it; version control remembers.
- `TODO` and `FIXME` markers are not descriptive comments. Leave them alone.

## Verify every claim

Inline comments are prone to be outdated. For each comment asserting something about the code, check that it is true.
Typical issues:

- **Direction and mapping.** "X becomes Y", "converted back to Z". Read the operation and confirm which way is true.
- **Attribution.** An effect credited to a named class, flag, constant or setting. Confirm that the code in view actually
  carries the thing named, and that the thing named has the effect claimed.
- **Values and shapes.** A stated threshold, unit, default, type or return shape. Compare it against the signature and
  the constant.
- **Cross-references.** A named function, file or field. Confirm it still exists under that name.

Where comment and code disagree, work out which one is wrong. If it is the code, report it and change neither.

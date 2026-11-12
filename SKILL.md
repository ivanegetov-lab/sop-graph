---
name: sop-graph
description: Turn a folder of procedures (SOPs, work instructions, quality, safety and maintenance procedures, as PDF or Word) into a knowledge graph of how the plant is run, with an interactive map, a plant summary to give an AI assistant, a queryable database, and a review report of contradictions, dead references and training gaps. Use when someone wants to map their SOPs, find conflicts between procedures, see what a change affects ("we're changing supplier / a machine / a setting, which procedures need updating?"), prepare documents for an audit, or give an AI assistant their procedures as context.
argument-hint: "[folder of procedure documents]"
allowed-tools: Bash, Read, Write, Glob, Grep
---

# SOP graph

Procedures are written one at a time, by different people, in different years. Nobody sees how they connect. This skill reads the whole set and builds one graph: every procedure, and the machines, materials, tools, roles, forms and other procedures it touches.

What comes out (in one output folder):

- **`graph.html`**: the interactive map. Type what you are changing and everything it touches lights up. Lists the problems found.
- **`plant-summary.md`**: a readable summary to give an AI assistant as context.
- **`graph.json`** and **`graph.db`** (SQLite): the full graph, to query or load elsewhere.
- **`qa-report.md`**: contradictions, references to documents that aren't there, old revisions, people with jobs in procedures they aren't trained on, and everything that was unclear.

**The rule that makes it trustworthy: you read, the script connects and checks.** You extract what each document says, with the place and a word-for-word quote. `scripts/sop_graph.py` merges, compares and builds. You never decide two documents conflict from memory; the script puts them side by side and you rule on what it shows.

## Step 1. Look at the documents

List the folder. PDFs can be read directly with the Read tool (scanned ones too). For Word files run `python3 scripts/docx_text.py file.docx`. Then, if `pdftoppm` and `pdftotext` are installed (poppler), make page images and text dumps:

```bash
python3 scripts/sop_graph.py pages --docs <folder> --out work/pages
```

The images appear in the map. The text is used to check your quotes. Both are optional.

## Step 2. Extract each document

Read `references/schema.md` first. Then, one document at a time:

1. Read the whole document. Every page.
2. Write `work/extracted/<document number>.json`.
3. After every two or three documents run `python3 scripts/sop_graph.py names --extracted work/extracted` and reuse the names it prints. The conflict checks only work when the same thing has the same name.

What matters most:

- **Take every cross-reference**, including ones buried in a step ("as described in SP-402"), and any revision letter given with it.
- **Take every number someone is told to hit or check** as a parameter, with its quote.
- **Take every statement of who may or must do something** that another document could contradict, as a rule.
- **Quote exactly.** Don't tidy the wording.
- **When you can't read it or aren't sure, put it under `unsure`.** Don't guess.
- For more than about 15 documents, split the set between subagents, give each the schema and the `names` output, and run `names` again when they finish to line up wording.

## Step 3. Check and rule

```bash
python3 scripts/sop_graph.py check --extracted work/extracted --pages work/pages
```

Read the output:

- `issues`: what the script is sure about.
- `to_decide`: topics that appear in more than one document. Open both documents, read the passages, and write your ruling in `work/review.json` (`conflict` or `ok`, with the reason).
- `quote_check`: quotes it could not find in the document text. Fix each one in the extraction file.

Then read across the set for what a script can't see and add it to `review.json` as a finding, with evidence from both documents. The two most valuable kinds:

- a requirement in one document with no matching step in the document that should carry it out;
- a step that relies on something another document has since removed or changed.

If two names are certainly the same thing written two ways, add them to `work/aliases.json`. Never merge roles or materials on a guess.

## Step 4. Pick the example and build

Write `work/story.json` with a title and one example change the plant could really face (see the schema). Then:

```bash
python3 scripts/sop_graph.py build --extracted work/extracted --pages work/pages \
  --review work/review.json --aliases work/aliases.json --story work/story.json --out out
```

Open `out/graph.html`.

## Step 5. Check before you hand it over

1. `quote_check.not_found` is 0, or each remaining one is explained.
2. Nothing is left under "Still to decide" in `qa-report.md`.
3. Open the map. Type the example change and read the list it gives. Click two problems and confirm the quotes are what the documents say.
4. Tell the user: how many documents were read, how many items need review, which are the three most serious and why, and what you were unsure about. **The graph still needs review by someone who knows the plant**, most of all where a document was scanned or unclear.

## Files

- `scripts/sop_graph.py`: `pages`, `names`, `check`, `build`. Python 3 standard library.
- `scripts/docx_text.py`: text from a Word file.
- `assets/viewer.html`: the map page.
- `references/schema.md`: the extraction format, `review.json`, `aliases.json`, `story.json`.
- `examples/plant-2/`: 20 procedures written for the Plant 2 open dataset (a fictional packaging plant), the extractions, and the finished outputs.

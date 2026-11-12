# Extraction schema

Write one JSON file per document into the `extracted/` folder, named after the document number (`WI-211.json`). Every list is optional; leave out what the document doesn't contain. Never fill a field from memory or from another document.

```json
{
  "doc": {
    "id": "WI-211",
    "title": "Capper Setup and Torque Check",
    "type": "Work Instruction",
    "rev": "C",
    "effective": "2022-11-07",
    "owner": "Production",
    "file": "WI-211 Capper Setup and Torque Check.pdf",
    "pages": 2,
    "purpose": "One sentence, in the document's own words."
  },
  "roles":      [{"name": "Operator", "does": "Sets up the capper and checks torque.", "where": "Roles table"}],
  "equipment":  [{"id": "CAP-2", "name": "Line 2 capper", "where": "Scope"}],
  "materials":  [{"name": "Caps (38 mm)", "where": "Materials"}],
  "tools":      [{"name": "Torque tester", "where": "Tools"}],
  "ppe":        [{"name": "Safety glasses", "where": "PPE"}],
  "forms":      [{"id": "FRM-PR-11", "name": "Torque Check Sheet", "where": "step 5"}],
  "products":   [{"id": "FS-2000", "name": "Fabric softener 2 L", "where": "Scope"}],
  "references": [{"id": "QP-315", "as_written": "QP-315 Nonconforming Product and Hold", "rev": null, "where": "step 7"}],
  "suppliers":  [{"material": "Labels", "supplier": "Northside Labels", "where": "Specifications table"}],
  "parameters": [{"what": "application torque", "applies_to": "38 mm cap", "value": "17", "unit": "in-lb",
                  "tolerance": "plus or minus 2", "where": "Application torque table", "quote": "Line 2 (CAP-2), both bottle sizes"}],
  "rules":      [{"topic": "who may change the fill setpoint", "statement": "Only the Maintenance Technician changes the setpoint.",
                  "where": "step 7", "quote": "Operators must not change the fill setpoint."}],
  "training":   [{"role": "Operator", "docs": [{"id": "WI-211", "rev": "A"}], "where": "Required procedures by role"}],
  "unsure":     [{"what": "Torque for the 28 mm cap is smudged", "why": "Scan is unreadable in the table", "where": "page 2"}]
}
```

## Field rules

- **`doc.id`**: the document number exactly as printed. `effective` as `YYYY-MM-DD`. `rev` as printed.
- **`where`**: the section name or step number a reader would use to find it ("step 6", "Scope", "Fill targets table").
- **`quote`**: the document's exact words, 25 words or fewer, as one unbroken run from one line or one table cell. No "..." and no stitching two places together. Required for `parameters` and `rules`. The build compares quotes with the PDF text and reports any it cannot find, so copy, don't paraphrase. For a number in a table, quote the cell or the row label next to it.
- **`roles`**: everyone the document gives a job to, including roles that only appear in a step. One entry per role. Use the name as written ("Shift Lead" stays "Shift Lead" even if you suspect it is the same as "Line Lead"; the build flags likely matches for a person to decide).
- **`equipment`**: use the tag as `id` (`CAP-2`). A range ("FL-01 to FL-04", "DOCK-1 to DOCK-4") becomes one entry per tag. Equipment with no tag gets a `name` only.
- **`materials`, `tools`, `ppe`**: short singular-or-plural names as written. Run `names` first and reuse an existing name when the document means the same thing.
- **`forms`**: records the document tells people to fill in. `id` is the form number. A record with no number ("Maintenance work order") gets a `name` only.
- **`products`**: products or part numbers the document applies to, when it names them.
- **`references`**: every other controlled document mentioned anywhere, by number. If the text gives a revision ("SP-402, Rev B"), put it in `rev`. Do not list the document itself, forms, or equipment. A reference with no number ("the cap setup instructions") goes under `unsure`; don't guess which document it means.
- **`suppliers`**: only where a document names who supplies a material.
- **`parameters`**: numbers people are told to hit or check: settings, limits, intervals, sample sizes, speeds, temperatures, times.
  - `what` is a short lowercase name of the quantity ("application torque", "fill weight check interval", "maximum speed").
  - `applies_to` says what it applies to ("38 mm cap", "forklifts inside the building", "FIL-1").
  - Two documents giving the same quantity must end up with the same `what` and `applies_to` wording, or the conflict check can't see them. Run `names` and reuse.
  - `value` is the number as a string; ranges go in `value` as written ("750 to 765"). Keep the unit as printed ("1" + "hour", "30" + "minutes"); don't convert.
  - If two documents give what looks like the same quantity measured at different points, still use the same `what` and `applies_to`. The script will put them side by side and you rule on it in `review.json`.
- **`rules`**: statements about who may or must do something, or what must never happen, that another document could plausibly contradict. `topic` is a short neutral label ("who may change the fill setpoint", "maximum forklift speed"). Reuse topics across documents. Don't record every instruction as a rule; ten good ones per set beat a hundred.
- **`training`**: only from documents that say which roles must be trained on which documents. Expand shorthand ("everything for Operator, plus QP-306") into the full list.
- **`unsure`**: anything you could not read or had to guess. It is better to list ten of these than to guess once. Don't repeat something here that you are also reporting as a finding.

## review.json

After `check`, decide every item under `to_decide` and add anything the script cannot see:

```json
{
  "decisions": [
    {"key": "rule:who may change the fill setpoint", "verdict": "conflict",
     "title": "Two answers to who may change the fill setpoint",
     "why": "WI-210 lets operators adjust by up to 2 g. QP-303 says operators must not change it."},
    {"key": "value:minimum vacuum", "verdict": "ok", "why": "Measured at different points: the erector cups and the pump inlet."}
  ],
  "findings": [
    {"type": "gap", "severity": "high", "title": "Critical check not in the inspection procedure",
     "detail": "QP-309 makes label liner caliper a critical characteristic measured on every lot. QP-308 lists the label checks and it is not among them.",
     "evidence": [{"doc": "QP-309", "where": "Specifications table", "quote": "..."}, {"doc": "QP-308", "where": "step 6", "quote": "..."}]}
  ]
}
```

- `verdict` is `conflict` or `ok`. Give the reason in one or two plain sentences that name both documents. `ok` is the usual outcome: most topics that appear in two documents agree.
- **Number conflicts** (`value_conflict`) are reported straight away without waiting for a ruling. `check` lists their keys under `value_conflict_keys`. Rule `ok` on one, with the reason, if the two numbers are not really the same quantity (different measuring points, different products).
- A decision may set `"severity"`; a finding should. **high**: following the documents as written could cause a safety, quality or compliance failure. **medium**: people could reasonably do it two different ways. **low**: housekeeping.
- A `finding` needs evidence from every document it names. Types: `gap`, `rule_conflict`, `value_conflict`.
- Look for gaps the script can't compute: a requirement in one document with no matching step in the document that should carry it out; a step that depends on something another document has since removed.

## aliases.json

Only for names that are certainly the same thing written two ways:

```json
{"tool": {"Check scale (0.1 g)": ["Check scale", "check scale 0.1g"]}, "role": {}}
```

Do not merge roles or materials on a guess. Leave them in the report for the plant to decide.

## story.json

```json
{"title": "How Plant 2 is run",
 "example": {"question": "We're switching label supplier. What needs updating?", "node": "Labels"}}
```

`node` is the exact name (or tag) of a node in the graph. Pick a change the plant could really face, on a node that several procedures touch.

# Reviewing translation structure validation

The overarching goal is that translated text retains the source document's structure while allowing the order of things within a paragraph to change for the target language's grammar. Judge a change by both sides of this contract: it must reject structural corruption and accept legitimate translation.

This guide covers `validator/structure.py` and integrations that render Markdown before calling it. It does not replace a human review of translation meaning.

## What stays fixed and what may move

| Content | Required behavior |
| --- | --- |
| Paragraphs, headings, lists, tables, tabs, steps, and callouts | Preserve element counts, block order, nesting, and protected attributes. |
| Wrappers containing blocks | Preserve their place in block order, even when the outer tag is normally inline, such as a link wrapping a heading. |
| Links, emphasis, images, and inline code within a paragraph | Allow grammatical reordering while preserving each element's identity, count, and nesting. |
| Inline elements next to blocks | Allow reordering within the same uninterrupted run; reject movement across a block boundary. |
| Code | Preserve exact code content, including whitespace. Inline code may move as a unit within a paragraph; code blocks remain ordered. |
| Link destinations and other protected attributes | Preserve values and their attachment to the corresponding element. Class order may vary in translation mode. |
| Placeholders in prose | Preserve identities and counts within the containing block. Allow movement between prose and inline text within that block. |
| Placeholders in `alt`, `title`, and `aria-label` | Preserve identities and counts separately in each attribute of the corresponding element. Surrounding prose or another attribute cannot compensate for a missing token. |
| Prose and accessible descriptions | Allow translation; preserve attribute presence and reject erased text where checked. |
| Platform tab labels | Preserve protected `iOS` and `Android` labels and tab identity. |

“Same structure” does not mean every inline node occupies the same sibling index. For example, accept this pair:

```html
<!-- Source -->
<p>Use <code>foo</code> before <code>bar</code>.</p>
<!-- Translation -->
<p>Vor <code>bar</code> nutze <code>foo</code>.</p>
```

Both immutable code strings are present once. Comparing the first source `<code>` with the first target `<code>` would incorrectly reject valid grammar. Apply the same reasoning when code is inside an emphasis or link wrapper. Replacing `foo` with another `bar` must still fail.

Reject moving a block-containing link across a paragraph:

```html
<!-- Source -->
<a href="/help"><h2>Help</h2></a><p>Instructions</p>
<!-- Invalid target -->
<p>Anleitung</p><a href="/help"><h2>Hilfe</h2></a>
```

Reject transferring an accessible-description placeholder into prose:

```html
<!-- Source -->
<p><img src="/photo" alt="Photo of {{name}}">Hello</p>
<!-- Invalid target -->
<p><img src="/photo" alt="Foto">Hallo {{name}}</p>
```

The document-wide token count is unchanged, but the image description lost its placeholder.

## How to review a change

1. Identify the comparison boundary. Is the change about document blocks, an inline run, an individual element, or an attribute? Check the rendered tree, including descendants of wrappers, instead of relying solely on the immediate tag name.
2. Check matching before comparison. Repeated inline tags must match by protected structure and immutable content, independent of grammatical position or translated wording. Include attribute presence and empty/nonempty content when matching repeated tags; otherwise a valid reorder can look like erased text. Keep multiplicity: sets alone lose duplicate elements and tokens. Attribute tokens must remain attached to their corresponding elements when those elements reorder.
3. Require an accepted translation example and a rejected corruption example for each rule. Overly strict validation is also a bug. Include repeated tags, nested wrappers, changed code, duplicated code, moved blocks, and tokens moved between attributes or between an attribute and prose.
4. Confirm renderer parity. Ordinary Markdown may use the default renderer. Custom tabs, steps, callouts, and directives must use the publishing application's renderer. Unrendered `:::` directives must not silently pass as prose. Literal directives inside fenced, indented, or inline code are valid examples; let the renderer identify those code regions.
5. Review translation mode and `preserve_text=True` separately. The latter checks migration parity, including prose and attribute values. Do not weaken it merely to accept a translation; use translation mode for translated content.
6. Verify the public API and JSON CLI. Cover accepted and rejected requests, batch result IDs, structured errors, and exit codes. An excessively nested document must fail with a structured error while other batch items still receive results. Run the existing tests as well as the new regressions.

Use TDD for fixes: add the smallest regression that expresses the contract, observe it fail on the original implementation, make the fix, then rerun the regression and relevant existing checks. Do not change expected outcomes merely to accommodate an implementation.

```sh
python -m pytest tests/test_structure.py
python -m pytest
flake8 validator/structure.py tests/test_structure.py
```

For a downstream integration, also run its adapter with real rendered articles and deliberate corruption. Report that evidence separately from synthetic validator fixtures.

## Limits to keep explicit

Structural validation cannot establish translation quality or semantic equivalence. If two paragraphs have identical markup and no distinguishing protected content, swapping only their prose may be indistinguishable from translation. Preserving meaning, instruction completeness, and the relationship between translated wording and a link requires language review.

Printf `%%` escapes a literal percent sign and is not a substitution. Placeholder scans must not join text from different blocks: `25%` at the end of one paragraph followed by “off” in another does not form `%o`. In migration-parity mode, preserve spaces inside inline elements when they separate visible words, while allowing layout whitespace between blocks.

The parser rejects common malformed fragments but is neither a sanitizer nor a complete HTML5 conformance checker. Placeholder recognition covers the documented brace and printf subset, not arbitrary template languages or full ICU messages. Do not claim these broader guarantees from a passing structural check.

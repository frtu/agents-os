<!--
pdf-extract output template: edit this file to change the Markdown body written next to each PDF.
No code change is needed. Existing .md files are only rewritten when their PDF changes, so re-run with --force to apply an edit to them.

The frontmatter (source_sha256, generator, ...) is NOT here: it is a machine contract the script reads back, so it stays in code.

Sections: each one starts with a marker line on its own (`@document`, `@page`, `@empty-page` inside an HTML comment, as below).
Everything above the first marker (this note) is ignored. Blank lines around a section are trimmed.

  @document     the whole body. {{TITLE}} = PDF title or file name, {{PAGES}} = every rendered page, joined by a blank line
  @page         one page. {{PAGE_NUMBER}}, {{METHOD}} (extraction method + notes), {{TEXT}} (page text, fenced or raw per --body)
  @empty-page   what {{TEXT}} becomes when a page has no text

An unknown {{PLACEHOLDER}} is left visible in the output. Use another template with --template PATH.
-->
<!-- @document -->
# {{TITLE}}

{{PAGES}}

<!-- @page -->
## Page {{PAGE_NUMBER}}

<!-- method: {{METHOD}} -->

{{TEXT}}

<!-- @empty-page -->
_(no text found on this page)_

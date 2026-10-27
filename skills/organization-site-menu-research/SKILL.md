---
name: organization-site-menu-research
description: Assess organization-site navigation labels with evidence.
version: 0.1.0
author: office
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [information-architecture, navigation, nonprofit, research]
    related_skills: [codebase-inspection, grounded-citations]
---
# Organization-Site Menu Research

Use this workflow to recommend or evaluate a website menu label for an organization. Research only unless implementation is explicitly requested.

## When to Use
- A user asks what a site menu means or what should replace it.
- A navigation label may represent editorial content, an operational service, or an organization program.

## Procedure
1. **Inspect project truth first.** Read the product brief, information architecture, and relevant content model before recommending a label. Record whether the spec is approved or still draft.
2. **Verify live implementation.** Use the code graph before source inspection when available. Confirm what the page actually contains, who manages it, and whether it is public, admin-only, or both. Do not infer behavior from its title.
3. **Separate distinct user needs.** Distinguish editorial publishing, programs/activities, and user feedback. A comment or suggestion workflow requires ownership, response expectations, moderation, and privacy handling; it is not equivalent to an editorial section.
4. **Compare a small set of labels.** For each option, state what content belongs there, visitor benefit, cost/risk, and conditions under which it fits. Check for duplicate existing sections.
5. **Ground benchmarks.** Prefer official peer-organization navigation and reputable information-architecture guidance. Treat examples as patterns, not universal proof. Cite direct URLs and the actual menu categories observed.
6. **Recommend conditionally.** Choose the label that matches both documented organizational goals and verified content. If real program details are absent, do not relabel editorial drafts as programs; require owner validation and preserve/archive existing content rather than deleting it.
7. **Respect delivery gates.** Keep research separate from implementation. Do not change routes, content, or data unless requested and allowed by the project phase and touch-path constraints.

## Implementing the chosen label (only when explicitly asked)
1. **Find every surface first.** Public menu, mobile menu, footer, home cards, detail views, sitemap, default settings/CTA copy, page `<title>`/meta, FAQ copy, panel labels, and tests. A rename that touches only the nav leaves contradictory copy behind.
2. **Keep internal names, change public names.** Model, table, panel path, and CSS hook classes can keep the old word; renaming them forces data migrations and widens the diff. Document the mapping in the commit or evidence note.
3. **Serve the canonical URL and 301 the old one.** Resolve the old slug through the model so stale slugs redirect to the canonical slug, and fall back to the section index instead of returning 404 or 500.
4. **Never let drafts become links.** Build navigation labels from a fixed field list plus a `published()` lookup, render unpublished entries as `<span aria-disabled="true">`, and give draft detail pages a neutral "not published yet" view with no title/thesis/body.
5. **Update tests in the same commit.** Route smoke tests, crawl checks, content gates, SEO/QA, and menu matrix all hardcode the old paths; convert them to the canonical path plus an explicit 301 assertion, otherwise the suite fails or silently stops covering the section.
6. **Re-run the visual check.** Take desktop and mobile screenshots, force lazy images to load before capturing, and confirm no placeholder copy, no overflow, and no leftover old label.
7. **Check test argument order.** Live tests taking positional CLI arguments (e.g. process count, capacity) will silently pass a URL as an integer and report a false failure; read the header before running.

## Verification
- Explain the existing menu in plain language.
- Tie the recommendation to project goals and actual content.
- Include evidence from project documents and external sources.
- State trade-offs, prerequisites, and any unresolved owner decision.
- Make no unrequested code or data changes.
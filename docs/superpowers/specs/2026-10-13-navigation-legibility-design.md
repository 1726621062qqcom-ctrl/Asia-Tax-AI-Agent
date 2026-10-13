# Navigation and source-panel legibility

The desktop workspace currently renders several actionable labels at 10–12 px. The user identified the left history/account area and right sources panel as hard to read. Increase primary control text in those areas to about 14 px, and supporting labels to at least 12 px. Preserve the current color system, spacing rhythm and behavior.

Adjust the CSS at its existing source selectors, including later `auth.css` and `chat-polish.css` overrides. Widen the desktop sidebar and sources panel modestly so larger labels and email addresses do not crowd the conversation. Keep responsive drawer behavior at narrow widths; long email addresses and source titles must remain safely clipped or wrapped. No API or content changes are involved.

Verify the production frontend build and existing browser interaction tests. Inspect the final CSS values and responsive layout. This is a visual readability change, so no new behavior tests are required.

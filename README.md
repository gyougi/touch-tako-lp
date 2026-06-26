# Touch Tako — Landing Page

Marketing landing page for **Touch Tako タッチタコ**, a native macOS touch-typing
game for kids (octopus mascot). Single-file static site.

- `index.html` — the whole page (inline CSS + i18n JS).
- `icon.png` — app icon (256×256).

## Languages

Japanese / English / Simplified Chinese, switchable in-page. First visit follows
the browser's language; the manual toggle changes the current view only.

## Local preview

```sh
python3 -m http.server 8135
# → http://localhost:8135
```

## Notes

- The "Coming soon to the Mac App Store" button is a placeholder until the app is
  live. Search `TODO` in `index.html` for the two spots to swap in the App Store
  URL once it has an ID.
- Legal/support pages live in the separate `touch-tako-legal` repo, linked from
  the footer.

© 2026 GLSPACE

# Changelog

## 0.2.0 — 2026-10-15
- **Playground** at renaissancexbt.github.io/pixelsort: drop a photo, live sliders, presets,
  "watch it sort" animation, MP4/WebM recording, PNG download, live webcam mode. One HTML file,
  runs entirely in the browser.
- `--animate OUT.mp4|OUT.gif`, `--seconds`, `--fps`: render the sort as a video. Odd-even
  transposition inside the same runs; the last frame equals the still image.
- `animate` optional extra (numpy).

## 0.1.0 — 2026-10-14
- Keys: lightness, intensity, hue, saturation, red, green, blue
- Intervals: threshold, edges, random, none
- Any sorting angle, masks, seeded randomness
- `pixelsort` CLI, 17 tests, CI on Python 3.10 and 3.12

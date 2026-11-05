# SPEC: SlideMarks, "One slide, two lives"

GOAL:    a PowerPoint user feels the icon grind they know, then sees symbols that behave like text,
         then learns it works in Word too. They remember: "Harvey balls you can type."
OUTPUT:  HyperFrames, 1920 x 1080, 30 fps
TIME:    64 s x 30 = 1920 frames. Music: ticking bed 0–21.2 s, silence on the question, bright bed from the mark (22.85 s), silence under "One more thing…", back at 54 s.

LOOK
- Ground: `#f6f8fa` (site panel), flat, no texture, no gradient. Slides and windows sit on it.
- Window: real screenshot, radius 14 px, shadow 0 30px 80px rgba(31,35,40,.16), 1px `#d1d9e0` edge.
- Slide card (rebuilt close-ups): `#ffffff`, radius 10, same shadow; table hairlines 2px `#d1d9e0`,
  header row `#f6f8fa`, header text `#59636e` 26px/700, body text `#1f2328` 38px/400.
- Ink `#1f2328`, muted `#59636e`. Accent `#6d3b8e` (site) only on: the one highlighted word per
  title, Product A glyphs, the reveal and the end card. Mark: harvey-75 glyph in `#9b5cc8`
  (the add-in's own ribbon icon colour).
- Type: Inter 800 for titles, 76 px (7% of height), tracking -2%; one line, max 6 words.
  Inter 400 for body. Every symbol on screen in the "after" is the real SlideMarks font (woff2 from
  dist/web). "Before" icons are PNGs rasterised from the same glyph SVGs (they stand in for pasted
  pictures).
- Titles live in a caption slab: white, 1px `#d1d9e0`, radius 14, bottom-left inside title-safe,
  never over a dimmed screenshot.

OBJECTS
- PowerPoint window (real captures, light mode): Icons search "harvey ball" with no match;
  "pie chart" with near-miss icons; a 1" x 1" icon dropped across two rows; the finished broken slide.
- SlideMarks pane (real capture, cropped) beside the rebuilt table.
- Word window with the pane open (real capture).
- Cursor: macOS arrow, 46 px tall, black with 3 px white edge.

MOTION
- Camera (punch-ins on screenshots): 0.6 s `power2.inOut` on a wrapper's scale/x/y.
- Arrivals `expo.out` 0.5 s; exits 0.25 s `power3.in`; title words blur 6px→0, 0.067 s apart.
- Before side: icons drop big (110 px, handles), then shrink to cell with `back.out(1.6)` and land
  2–9 px off. After side: glyphs arrive as a typed character with a 1-frame caret, no bounce.
- Row growth: 0.5 s `power2.inOut`; rows below move with it; before-icons do not.

SHOTS (seconds)
1. hunt 0–9.6: nomatch (push table → search message) · pie (near-misses) · dropped (1" icon, H/W boxes).
   Titles: "Need a Harvey ball?" / "Try “pie chart”…" / "Insert. Resize. Nudge."
2. grind 9.6–19: rebuilt table; 10 icons inserted and nudged, accelerating; GDPR text grows;
   icons stay. Titles: "Ten cells, ten pictures." / "Then the text changes." / "The icons don't."
3. real 19–21: real broken slide, punch-in on drifted icons. Title "Every edit. Every slide."
4. reveal 21–24.5: "What if the symbol was just text?" → mark fills, "SlideMarks".
5. demo 24.5–40.5: table + real pane; pick → insert → fill; text grows; align; size; B/I/U; colour.
   Titles: "Pick it. It's text." / "Text grows. Symbols follow." / "Align it like text." /
   "Size it like text." / "Bold. Italic. Underline."
6. inline 40.5–47.5: top card: a picture lands at the start of a text box, "Fully compliant" is
   typed and runs underneath it; spaces, drag, nudge to fix. Bottom card: click in the box, pick
   Harvey 100% in the real pane, Insert, type: the symbol leads the words. Titles "Add an icon.
   Type." / "It's hidden." / "Space. Drag. Nudge." / "Click. Type. Done."
7. payoff 47.5–51: wipe broken → clean on one table. Claim: "Symbols that behave like text."
8. onemore 51–54: "One more thing…"
9. word 54–59.5: real Word + pane; push to the inline "SSO ✓". Title "Works in Word too."
10. end 59.5–64: mark fills 0→75 %, wordmark wipes, "Free for Word and PowerPoint", URL. Hold 2.5 s.

BANNED: dark void ground; glow, particles; purple/blue gradients; glass; cream paper + serif;
mono caps labels; pill chips; everything centred; every element fade-slide-up; title over a dimmed
screenshot; logo docked in a corner; three cards in a row; any invented Office UI (the PowerPoint
and Word frames are captures only); invented numbers (no click counts, no "x faster").

QA: 1.0 (nomatch readable), 4.5 (pie icons), 8.0 (H/W 1"), 16.5 (broken grid), 20.0 (real slide),
23.5 (mark), 26.5 (glyph lands in cell), 31.0 (row grown, glyphs centred), 38.5 (B/I/U on row),
42.3 (text under picture), 46.8 (symbol + text), 48.6 (wipe mid), 52.5, 57.0 (Word inline symbol), 63.0 (end card).

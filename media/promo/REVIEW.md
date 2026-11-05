# REVIEW: cut 1 with sound (64 s)

## Creative calls
- Storyline A, "One slide, two lives" (picked by the user). B (split-screen race) and C (the icon
  that wouldn't move) are in STORYLINES.md.
- Real captures for everything that claims to be Office: PowerPoint icon search ("harvey ball":
  no match; "pie chart": near-misses), the 1" icon dropped across two rows, the finished broken
  slide, the SlideMarks pane (embedded, all green), the Home ribbon with font "SlideMarks" 28, Word
  with the pane. Captured in light mode (Office's own toggle, restored afterwards).
- Rebuilt in HTML only where something has to move: the table close-ups and the inline text
  boxes. Every "after" symbol is the real SlideMarks woff2; every "before" icon is a PNG of the same
  glyph SVGs, standing in for a pasted picture.
- Two small state overlays on real UI: the ribbon's align/B/I/U highlight and the font-size number
  (28→40→32). Nothing else on the captures is painted over.
- Inline beat added at the user's request: picture + typed "Fully compliant" (the words run
  under the picture, then spaces/drag/nudge) vs click, insert, type.

## Measured vs looked at
- `check` passes. Looked at: every beat frame, every seam (±0.2 s) and the 360 px phone sheet.
- Sound measured, not heard: render is -16.1 LUFS integrated, -2.7 dBTP, no clipping; onsets
  line up with the icon inserts (10–15 s) and the reveal (22.9 s); silence under "One more thing…".
- Rendered: `renders/slidemarks-promo.mp4` (1920x1080, 30 fps, delivery quality, 8.7 MB).

## Kept warnings
- `text_below_floor` on `#d-size` (21 px): it is the real ribbon's size box at real proportion;
  the change is carried by the table, not by reading the number.

## Weakest shots / next
- The reveal → demo seam is a cut from the lockup to an empty ground for a few frames before
  the workspace blurs in; could carry the mark into the pane icon instead.
- Hunt shot A opens mid-zoom on the slide; a frame-0 thumbnail with the caption already landed
  would be stronger.
- Music entry points were picked from loudness windows, not by ear; the after-bed enters at
  12 s into its track and resumes at 40 s after the "One more thing…" silence. Worth a listen.
- One SFX is CC BY (click1): credit it wherever the video is published (CREDITS.md).

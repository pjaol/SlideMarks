# media/

Promo video for SlideMarks: "One slide, two lives" (before/after, then Word).

- `capture/`: `build_decks.py` builds the PowerPoint/Word files that were opened in Office and
  screen-captured; `raw/` holds those captures (light mode; `raw/dark/` is an earlier dark-mode set).
- `promo/`: the HyperFrames project. `STORYLINES.md` (the three pitches), `SPEC.md` (the build brief),
  `index.html` + `compositions/` (scenes), `assets/` (captures, font, icons).

Preview: `cd promo && npx hyperframes preview`. Render: `npx hyperframes render`.

Capture notes: the add-in pane needs `uv run slidemarks office-serve` running. after.pptx/after.docx
were saved with "Embed fonts in the file" on so the pane shows its all-green state.
- Rendered video: `promo/renders/slidemarks-promo.mp4`. Audio credits: `promo/CREDITS.md` (one CC BY credit required).

Not in git (see .gitignore): renders, HyperFrames caches, the generated decks (rebuild with
`build_decks.py`) and the audio in `promo/assets/bgm` + `promo/assets/sfx` (HeyGen catalog / Openverse,
licensed for use in the video, not for redistribution). To restore the audio, re-run
`npx hyperframes media-use resolve --type bgm|sfx` with the intents in `promo/CREDITS.md`, then trim
and normalise as noted there (before.wav: bgm_004 from 5 s for 22 s, loudnorm -17 LUFS;
after.wav: bgm_002, loudnorm -16 LUFS; SFX peak-normalised to -3/-4 dBFS).

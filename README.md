# Why You Want Success But Keep Choosing Comfort

Private motion-first production source. Preserved 1,975-word script; selected user artwork; actual Flux Cole narration; script-aware Nova-3 word estimates; 165 designed motion scenes; Montserrat typography; stable active-word captions; neural 4× FSRCNN reconstruction; ducked synthesized music and cue SFX.

## Reproduce
Install Python 3.12+, numpy, pillow, opencv-contrib-python-headless and FFmpeg. Run `python upscale_art.py` and `python v2/render_motion.py` with start, stop and output arguments. Render parts without audio, concatenate in order, then mux `assets/mix.flac` once. `timeline.json` has actual duration. The workflow renders four persistent parts, assembles and verifies 1920×1080/30fps, and uploads `final-master`. A workflow artifact is not a release.

Narration source is preserved as lossless FLAC; all pause trimming/DSP occurred before STT. Timestamps are estimates: 99.24% normalized script-word match; interpolation exceptions are explicitly logged. `v2/panel_sync_review.md` logs actual cue timing and every panel used/omitted. No fake empirical quantities or quality scores.

No credentials or private instruction exports are committed. Fonts include their OFL license. Source artwork is user-supplied; generated binaries are published only as versioned release assets after review.

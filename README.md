# alturalab-video-tools

Local generator for the Altura LAB "MY VOLLEYBALL WEEK" reel (1080x1920, 30 fps, 18 s).
Frames are drawn with Pillow, the soundtrack is synthesized with numpy (no samples, no third-party audio) and ffmpeg encodes the MP4. No network or API calls.

## Setup
    python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
    mkdir -p tools/fonts
    cp "$(.venv/bin/python -c 'import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())')" tools/ffmpeg
    # Put Inter 4.0 (SIL OFL) OTF files in tools/fonts/:
    # Inter-Bold, Inter-SemiBold, Inter-Italic, InterDisplay-BlackItalic, InterDisplay-ExtraBoldItalic
    # https://github.com/rsms/inter/releases/tag/v4.0 (extras/otf/)

## Render
    ./render.sh [name.mp4]    # writes to renders/

Releases of this repository carry the rendered videos used for scheduling.

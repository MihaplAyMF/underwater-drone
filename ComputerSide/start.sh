
#!/bin/bash

# Force Qt to use X11 instead of Wayland
export QT_QPA_PLATFORM=xcb
export XDG_SESSION_TYPE=x11  # Optional: only if some libraries check this

# Optional: unset Wayland-specific variables to avoid interference
unset WAYLAND_DISPLAY

# Activate virtualenv
source ../.venv/bin/activate

# Start the main script
python main.py


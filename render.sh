#!/bin/zsh
# Renders the reel locally. Output goes to renders/ and never overwrites an existing file.
cd "${0:A:h}" || exit 1
exec .venv/bin/python source/make_v2.py "$@"

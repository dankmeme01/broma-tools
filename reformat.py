# Parses a broma file, reformats it, and dumps it
# Run as: python parse-and-dump.py <input> [output]
# If output is not specified, it will overwrite the input file

import broma
import sys
from pathlib import Path

file = broma.parse(sys.argv[1])
file.sort_everything()

text = file.dump()

if len(sys.argv) == 2:
    Path(sys.argv[1]).write_text(text)
else:
    Path(sys.argv[2]).write_text(text)

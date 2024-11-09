# Parses a broma file and dumps with no changes
# Run as: python parse-and-dump.py <input> <output>

import broma
import sys
from pathlib import Path

file = broma.parse(sys.argv[1])

text = file.dump()

Path(sys.argv[2]).write_text(text)

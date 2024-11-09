# Clears all offsets in a broma file
# Run as: python clear-offsets.py <input> <output>

import broma
import sys
from pathlib import Path

file = broma.parse(sys.argv[1])
for class_ in file.classes:
    for part in class_.parts:
        if isinstance(part, broma.BromaFunction):
            # keep inlined defs
            part.binds = {bind: part.binds[bind] for bind in part.binds if part.binds[bind] is None}

text = file.dump()

Path(sys.argv[2]).write_text(text)

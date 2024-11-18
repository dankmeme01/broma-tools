# Parses broma files and shows warnings
# Run as: python warn.py <files...>
# aaa mongus this does not work yet

import broma
import sys
from pathlib import Path
import utils

bromas = []

first_file = Path(sys.argv[1])
if first_file.exists() and first_file.is_dir():
    for file in first_file.iterdir():
        bromas.append(broma.parse(file))
else:
    for file in sys.argv[1:]:
        bromas.append(broma.parse(file))

merged = broma.merge(bromas)

def warn(text: str) -> str:
    print(utils.color.yellow('! WARN: ' + text))

def minor_warn(text: str) -> str:
    print(utils.color.yellow('NOTE: ' + text))

def get_all_overloads(file: broma.Broma, cls: broma.BromaClass) -> dict[str, list[broma.BromaFunction]]:
    overloads = {}

    for basestr in cls.bases:
        base = file.find_class(basestr)
        if not base:
            continue

        for name, funcs in get_all_overloads(file, base).items():
            if name not in overloads:
                overloads[name] = []

            overloads[name].extend(funcs)

    for part in cls.parts:
        if not isinstance(part, broma.BromaFunction):
            continue

        overloads.get(part.name, []).append(part)

    return overloads


for cls in merged.classes:
    overloads = get_all_overloads(merged, cls)

    for name, funcs in overloads.items():
        if len(funcs) > 1:
            has_virtual = False
            has_non_virtual = False

            for func in funcs:
                if 'virtual' in func.attrs:
                    has_virtual = True
                else:
                    has_non_virtual = True

            if has_virtual and has_non_virtual:
                warn(f"{cls.name}::{func} has overloads both virtual and non-virtual overloads")
                warn("This can cause to incorrect vtable generation, check the vtable manually")

# write it to a file

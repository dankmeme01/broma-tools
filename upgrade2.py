# Merges two broma files i think

import broma
import sys
import copy
from pathlib import Path

if len(sys.argv) != 4:
    print(f"Usage: {sys.argv[0]} <old_broma> <new_broma> <output>")
    exit(0)

print("NOTE: when you see 'Remove manually' in the output, this can mean two things:")
print("1. This is a helper function defined by the community. Do not remove it in that case.")
print("2. This is a function that was actually removed from a new version of the game. In that case, you should remove it.")
print()

old_file = broma.parse(sys.argv[1])
new_file = broma.parse(sys.argv[2])

# Use old file as a base, use new file to fixup function signatures, return types, add new functions/classes, remove ones that are gone.

to_insert = []

prev_cls = None
for new_cls in new_file.classes:
    old_cls = old_file.find_class(new_cls.name)

    # if it's a new class, continue and insert it later
    if not old_cls:
        print(f"Adding new class: {new_cls.name} after {prev_cls.name if prev_cls else None}")
        to_insert.append((copy.deepcopy(new_cls), prev_cls.name if prev_cls else None))
        prev_cls = new_cls
        continue

    prev_cls = new_cls

    # check for functions that were removed or sigs were changed
    to_remove_fns = []
    for idx, old_func in enumerate(old_cls.parts):
        if not isinstance(old_func, broma.BromaFunction):
            continue

        if old_func.is_constructor(old_cls.name) or old_func.is_destructor(old_cls.name):
            continue

        new_func = new_cls.find_function(old_func.name, old_func.get_arg_types())

        if not new_func:
            # if there is no new function with same arg types, check if there is a new function with same name AND there is only 1 overload in both old+new
            new_func = new_cls.find_function(old_func.name)

            if new_func and old_cls.overload_count(old_func.name) == 1 and new_cls.overload_count(old_func.name) == 1:
                old_cls.parts[idx] = copy.deepcopy(new_func)
                continue

            to_remove_fns.append(old_func)

    for fn in to_remove_fns:
        pass
        # if the function has no binds, it is probably a helper function, do nothing
        if fn.binds:
            print(f"Remove manually: {old_cls.name}::{fn.name}({', '.join(fn.get_arg_types())})")
        # old_cls.parts.remove(fn)

    # check for new functions
    for new_func in new_cls.parts:
        if not isinstance(new_func, broma.BromaFunction):
            continue

        old_func = old_cls.find_function(new_func.name, new_func.get_arg_types())

        if not old_func:
            if 'pure_virtual_' in new_func.name:
                print(f"Not adding {old_cls.name}::{new_func.name}({', '.join(new_func.get_arg_types())})")
                continue

            print(f"Adding function: {old_cls.name}::{new_func.name}({', '.join(new_func.get_arg_types())})")
            old_cls.parts.append(copy.deepcopy(new_func))

for (new_cls, insert_after) in to_insert:
    idx = -1
    for n, cls in enumerate(old_file.classes):
        if cls.name == insert_after:
            idx = n
            break

    if idx != -1:
        old_file.classes.insert(idx + 1, new_cls)

# Remove classes that were removed

to_remove = []
for old_cls in old_file.classes:
    new_cls = new_file.find_class(old_cls.name)

    if not new_cls:
        to_remove.append(old_cls)

for cls in to_remove:
    print(f"Not removing class: {cls.name}")
    # old_file.classes.remove(cls)

# Dump the file
old_file.sort_everything()
dumped = old_file.dump()
Path(sys.argv[3]).write_text(dumped)
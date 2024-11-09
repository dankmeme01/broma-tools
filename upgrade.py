# Merges two broma files i think
# NOTE: unfinished, dont use it
import broma
import sys
import copy
from pathlib import Path

if len(sys.argv) != 4:
    print(f"Usage: {sys.argv[0]} <old_broma> <new_broma> <output>")
    exit(0)

old_file = broma.parse(sys.argv[1])
new_file = broma.parse(sys.argv[2])

for new_cls in new_file.classes:
    old_cls = old_file.find_class(new_cls.name)

    # if it's a new class, do nothing
    if not old_cls:
        print(f"Skipping new class: {new_cls.name}")
        continue

    # add members, fix function arg & ret types

    comment_indices = []
    for idx, part in enumerate(old_cls.parts):
        if isinstance(part, broma.BromaFunction):
            new_func = new_cls.find_function(part.name, part.get_arg_types())

            # if it's a function that has been removed, don't do anything
            if not new_func:
                continue

            new_func.args = part.args
            new_func.ret_type = part.ret_type
        elif isinstance(part, (broma.BromaMember, broma.BromaPad)):
            # simply bring over
            new_cls.parts.append(copy.deepcopy(part))
        elif isinstance(part, broma.BromaComment):
            # todo ..
            comment_indices.append(idx)

    for idx in comment_indices:
        # backtrack to find estimately where to put this comment
        search_idx_rel = 1
        while search_idx_rel < min(idx, len(old_cls.parts) - idx):
            part_after = old_cls.parts[idx + search_idx_rel]
            part_before = old_cls.parts[idx - search_idx_rel]

            use_after = False
            use_before = False

            for i, p in enumerate(new_cls.parts):
                if p == part_after and (not isinstance(p, broma.BromaComment) or p.data):
                    use_after = True
                    break
                elif p == part_before and (not isinstance(p, broma.BromaComment) or p.data):
                    use_before = True
                    break
            else:
                search_idx_rel += 1
                continue

            # insert the comment here
            if use_after:
                new_cls.parts.insert(i, old_cls.parts[idx])
            elif use_before:
                new_cls.parts.insert(i + 1, old_cls.parts[idx])

            break

Path(sys.argv[3]).write_text(new_file.dump())

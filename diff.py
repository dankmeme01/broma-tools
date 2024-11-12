# Diff two broma files, not counting function offsets and inline bodies
# NOTE: this is quite shitty dont use it lol

import broma
import sys
import copy
import utils
from pathlib import Path

if len(sys.argv) != 3:
    print(f"Usage: {sys.argv[0]} <old_broma> <new_broma>")
    exit(0)

old_file = broma.parse(sys.argv[1])
new_file = broma.parse(sys.argv[2])

def print_green(text: str) -> str:
    print(utils.color.green('+' + text))

def print_red(text: str) -> str:
    print(utils.color.red('-' + text))

for new_cls in new_file.classes:
    old_cls = old_file.find_class(new_cls.name)

    # if it's a new class, print it
    if not old_cls:
        print_green(f"class {new_cls.name} {{")
        for part in new_cls.parts:
            if isinstance(part, broma.BromaFunction):
                print_green(f"    {part.dump()}")
            elif isinstance(part, broma.BromaMember):
                print_green(f"    {part.dump()}")
            elif isinstance(part, broma.BromaPad):
                print_green(f"    {part.dump()}")

        print_green("}")
        continue

    # diff the methods between two classes
    old_methods: list[broma.BromaFunction] = []
    new_methods: list[broma.BromaFunction] = []

    for part in old_cls.parts:
        if isinstance(part, broma.BromaFunction):
            old_methods.append(part)

    for part in new_cls.parts:
        if isinstance(part, broma.BromaFunction):
            new_methods.append(part)

    # check if everything is identical
    if old_methods != new_methods:
        print(f"class {new_cls.name} {{")

        for old_method in old_methods:
            if old_method not in new_methods:
                print_red(f"    {old_method.dump()}")
            elif (new_method := new_cls.find_function(old_method.name, old_method.get_arg_types())) != old_method:
                print_red(f"    {old_method.dump()}")
                print_green(f"    {new_method.dump()}")

        for new_method in new_methods:
            if new_method not in old_methods:
                print_green(f"    {new_method.dump()}")
            elif (old_method := old_cls.find_function(new_method.name, new_method.get_arg_types())) != new_method:
                print_red(f"    {old_method.dump()}")
                print_green(f"    {new_method.dump()}")

        print("}")

# check if any classes have been removed
for old_cls in old_file.classes:
    if not new_file.find_class(old_cls.name):
        print_red(f"class {old_cls.name} {{")
        for part in old_cls.parts:
            if isinstance(part, broma.BromaFunction):
                print_red(f"    {part.dump()}")
            elif isinstance(part, broma.BromaMember):
                print_red(f"    {part.dump()}")
            elif isinstance(part, broma.BromaPad):
                print_red(f"    {part.dump()}")

        print_red("}")
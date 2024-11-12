# broma-tools

Scripts for parsing and serializing broma (.bro) files.

Main attraction is `broma.py` - it's a library that has various utilities. TODO: better docs

## clear-offsets.py

Run as `python clear-offsets.py <input> <output>`, parses the broma at `input`, clears all function offsets (keeps inlines and pads intact!), and outputs to `<output>`

## diff.py

Show differences between two broma files. Incomplete, do not rely on it.

## parse-and-dump.py

Simply parses a broma file and outputs with no changes (except ones introduced by loss of information when parsing)

## reformat.py

Parses the broma file, reformats it according to some rules, and writes it to a specified destination, or to the same file.

## upgrade2.py

Given an older, community made broma file with filled members, inlined functions etc., and a clean broma file of a newer version, merges them to a broma file in a way so that:

* It preserves all of the inlined function bodies, unless their signature has changed.
* It preserves all the functions that are community added
* It preserves all the struct members and pads
* It preserves all (or most of) the comments
* It adds the classes and methods from the newer broma file that don't exist in the older one
* It reformats the broma file

# warn.py

Prints suspicious things that are detected in a broma file

# TODO

* c arrays members
* template function args aren't parsed correctly (but is ok in dump!)
* ret type should be separate from specifiers (but is ok in dump!)
# broma-tools

Scripts for parsing and serializing broma (.bro) files.

Main attraction is `broma.py` - it's a library that has various utilities. TODO: better docs

## clear-offsets.py

Run as `python clear-offsets.py <input> <output>`, parses the broma at `input`, clears all function offsets (keeps inlines and pads intact!), and outputs to `<output>`

## upgrade.py

unifinshed script todo

## parse-and-dump.py

Simply parses a broma file and outputs with no changes (except ones introduced by loss of information when parsing)

# TODO

* multi line function arguments
* c arrays members
* template function args aren't parsed correctly
* ret type should be separate from specifiers
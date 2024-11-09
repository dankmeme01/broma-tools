from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass, field
import re

__all__ = [
    "BromaMember"
    "BromaPad",
    "BromaFunction",
    "BromaClass",
    "Broma",
    "parse",
    "strip_line",
    "split_variable",
    "is_member"
]

class CharReader:
    def __init__(self, text: str) -> None:
        self.text = text
        self.idx = 0

    def peek(self) -> str:
        return self.text[self.idx]

    def peek_chars(self, n: int) -> str:
        return self.text[self.idx : self.idx + n]

    def skip_char(self):
        self.idx = min(self.idx + 1, len(self.text))

    def read_char(self) -> str:
        if self.idx >= len(self.text):
            raise ValueError("EOF")

        char = self.text[self.idx]
        self.skip_char()
        return char

    def read_chars(self, n: int) -> str:
        out = ""
        for _ in range(n):
            out += self.read_char()

        return out

    # read text until the sequence of characters is found (can be 1 char)
    def read_until(self, seq: str, include = False) -> str:
        out = ""

        found = False
        while self.idx + len(seq) < len(self.text):
            if self.peek_chars(len(seq)) == seq:
                found = True
                break

            out += self.read_char()

        if include and found:
            out += self.read_chars(len(seq))

        return out

    # read text until any char from the sequence is found
    def read_until_any(self, seq: str, include = False) -> str:
        out = ""

        found = False
        while self.idx + 1 < len(self.text):
            if self.peek() in seq:
                found = True
                break

            out += self.read_char()

        if include and found:
            out += self.read_char()

        return out

    def read_until_not_any(self, seq: str, include = False) -> str:
        out = ""

        found = False
        while self.idx + 1 < len(self.text):
            if self.peek() not in seq:
                found = True
                break

            out += self.read_char()

        if include and found:
            out += self.read_char()

        return out

    def skip_whitespace(self):
        while self.peek().isspace():
            self.skip_char()

    def skip_until(self, seq: str, include = False):
        self.read_until(seq, include)

    def skip_until_any(self, seq: str, include = False):
        self.read_until_any(seq, include)

    def skip_until_not_any(self, seq: str, include = False):
        self.read_until_not_any(seq, include)

    def skip_while(self, cond):
        while cond(self.peek()):
            self.skip_char()

    def peek_line(self) -> str:
        old_idx = self.idx
        text = self.read_until('\n', True)[0:-1]
        self.idx = old_idx
        return text

    def read_line(self) -> str:
        return self.read_until('\n', True)[0:-1]

    def skip_line(self):
        self.skip_until('\n')
        self.skip_char()

    def skip_comment(self) -> bool:
        if self.peek() == '/':
            if self.peek() == '/':
                self.skip_line()
                return True
            elif self.peek() == '*':
                self.skip_char()
                self.skip_until('*/', True)
                return True

        return False

    def skip_comments(self):
        while self.skip_comment():
            pass

    def skip_comments_and_whitespace(self):
        while True:
            self.skip_whitespace()
            if not self.skip_comment():
                break

def set_brace_level(old_level: int, line: str, paren: bool = False) -> int:
    chr1, chr2 = ('{', '}') if not paren else ('(', ')')
    return old_level + line.count(chr1) - line.count(chr2)

def indent_lines(text: str, spaces: int) -> str:
    lines = text.splitlines()
    out = ""
    for line in lines:
        out += " " * spaces + line + "\n"

    # remove last newline
    return out[:-1]

# strips line from single-line comments and whitespace
def strip_line(line: str):
    # remove comments
    if '//' in line:
        line = line[:line.index('//')]

    return line.strip()


# split a variable like 'void* m_member' into ('void*', 'm_member'), accounting for the positioning of asterisks in pointers
# this function is a monstrosity
def split_variable(var: str) -> tuple[str, str]:
    # if no variable, then just return the input as the type
    var = var.strip()
    if var.endswith('*') or var.endswith('&'):
        return (var, '')

    if ' ' not in var:
        return (var, '')

    # insert spaces if asterisk is in the wrong place (dont ask)
    last_asterisk = -1
    last_space = -1

    if '*' in var:
        last_asterisk = var.rindex('*')

    if ' ' in var:
        last_space = var.rindex(' ')

    if last_asterisk != -1 and last_space != -1 and last_asterisk > last_space:
        var = var[:last_asterisk] + '* ' + var[last_asterisk + 1:]

    identifier_pattern = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')

    parts = var.split()

    var_name = None
    type_parts = []

    for part in reversed(parts):
        if var_name is None and identifier_pattern.match(part):
            var_name = part
        else:
            type_parts.append(part)

    if var_name is None:
        var_name = ''

    type_string = ' '.join(reversed(type_parts))

    while ' *' in type_string:
        type_string = type_string.replace(' *', '*')

    return type_string, var_name

# syntax validation
def validate(cond, line_idx, message):
    assert cond, f"Syntax error on line {line_idx+1}: {message}"

global_validate = validate

def is_member(line: str):
    if ";" not in line or "{" in line:
        return False

    line = line.partition(";")[0]
    return '(' not in line and ')' not in line

@dataclass
class BromaMember:
    type: str
    name: str
    cpp_attributes: list[str] = field(default_factory=list)
    inline_comment: str = ""

    def dump(self) -> str:
        if self.cpp_attributes:
            ret = f"[[{', '.join(self.cpp_attributes)}]]\n{self.type} {self.name};"
        else:
            ret = f"{self.type} {self.name};"

        if self.inline_comment:
            ret += f" //{self.inline_comment}"

        return ret

@dataclass
class BromaPad:
    platforms: dict[str, int] = field(default_factory=dict)

    def dump(self) -> str:
        return f"PAD = {', '.join([f'{plat} {hex(self.platforms[plat])}' for plat in self.platforms])};"

@dataclass
class BromaComment:
    data: str
    force_multiline: bool = False

    def dump(self) -> str:
        if self.data is not None:
            if self.force_multiline or '\n' in self.data:
                return f"/*{self.data}*/"

            return f"//{self.data}"
        else:
            return None

@dataclass
class BromaPlatformBlock:
    platforms: list[str]
    code: str

    def dump(self) -> str:
        out = ""
        for platform in self.platforms:
            out += f"// {platform}\n"
        out += self.code
        return out

@dataclass
class BromaClass:
    name: str = "" # fully qualified class name
    attributes: list[str] = field(default_factory = list)
    parts: list[BromaFunction | BromaMember | BromaPad | BromaComment] = field(default_factory = list)
    bases: list[str] = field(default_factory = list)

    @classmethod
    def parse(cls, input: str, start_line: int) -> BromaClass:
        class_name = ""
        attributes = []
        parts = []
        bases = []

        inside_inlined_func = False
        current_inline_text = []

        inside_ml_comment = False # multiline comment
        current_ml_comment_text = ""

        inside_ps_block = False
        current_block_platforms = []
        current_block_text = []

        inside_func_signature = False
        current_func_signature_text = ""
        current_func_sig_brace_level = 0

        inside_inlined_func_signature = False
        current_inlined_func_signature_text = []

        next_member_attrs = []

        brace_level = 0

        lines = input.splitlines()
        for line_idx_rel, line in enumerate(lines):
            line_idx = start_line + line_idx_rel

            def validate(cond, message):
                global_validate(cond, line_idx, message)

            stripped_line = strip_line(line)

            # continuation of a multiline comment
            if inside_ml_comment:
                # if the comment ends here, add it and reset
                if '*/' in line:
                    inside_ml_comment = False
                    current_ml_comment_text += line.partition("*/")[0]
                    parts.append(BromaComment(current_ml_comment_text, True))
                    current_ml_comment_text = ""
                else:
                    current_ml_comment_text += line.strip("\n") + "\n"

            # start of a multiline comment
            elif '/*' in stripped_line and not inside_inlined_func:
                inside_ml_comment = True
                # if the comment ends on the same line, add it immediately
                if '*/' in line:
                    inside_ml_comment = False
                    text = line.partition("/*")[2].partition("*/")[0]
                    parts.append(BromaComment(text, True))
                else:
                    current_ml_comment_text = line.partition("/*")[2] + "\n"

            # single line comment
            elif line.strip().startswith("//") and not inside_inlined_func:
                text = line.partition("//")[2]
                parts.append(BromaComment(text))

            # empty line
            elif not line.strip() and not inside_inlined_func:
                parts.append(BromaComment(None))

            # attributes
            elif match := re.match(r"\[\[(.*)\]\]", stripped_line):
                att = [x.strip() for x in match.group(1).split(",")]
                if brace_level == 0: # class attributes
                    attributes += att
                else: # member attributes
                    next_member_attrs += att

            # class name
            elif match := re.match(r"class[\s]+([a-zA-Z0-9_]+(::[a-zA-Z0-9_]+)*)[\s]*:?[ ]*([a-zA-Z0-9_:, ]*)[\s]*{", stripped_line):
                validate(brace_level == 0, "nested class")

                class_name = match.group(1)
                bases_str = match.group(3)
                if bases_str:
                    bases = [x.strip() for x in bases_str.split(",")]

                brace_level = set_brace_level(brace_level, stripped_line)

                validate(brace_level == 1, "class did not immediately open its body")

            # inside inlined function
            elif inside_inlined_func:
                brace_level = set_brace_level(brace_level, stripped_line)
                current_inline_text.append(line)

                # if brace level goes back to 1, the function is over
                if brace_level == 1:
                    attrs = list(next_member_attrs)
                    next_member_attrs.clear()
                    inside_inlined_func = False
                    func = BromaFunction.parse_inlined(current_inline_text, class_name, attrs)
                    parts.append(func)

            # inside platform specific block
            elif inside_ps_block:
                brace_level = set_brace_level(brace_level, stripped_line)
                current_block_text.append(line)

                # if brace level goes back to 1, the block is over
                if brace_level == 1:
                    inside_ps_block = False
                    block = BromaPlatformBlock(current_block_platforms, '\n'.join(current_block_text))
                    parts.append(block)

            # inside inline definition of a function that has a multi-line function signature
            elif inside_inlined_func_signature:
                brace_level = set_brace_level(brace_level, stripped_line)
                current_inlined_func_signature_text.append(line)

                # if brace level goes back to 1, the function is over
                if brace_level == 1:
                    attrs = list(next_member_attrs)
                    next_member_attrs.clear()
                    inside_inlined_func_signature = False
                    func = BromaFunction.parse_multiline_signature_inlined(current_func_signature_text, current_inlined_func_signature_text, class_name, attrs)
                    parts.append(func)

            # inside function signature
            elif inside_func_signature:
                current_func_signature_text += line + "\n"
                current_func_sig_brace_level = set_brace_level(current_func_sig_brace_level, stripped_line, True)

                if current_func_sig_brace_level == 0:
                    current_func_signature_text = current_func_signature_text.strip(' \t\n{')
                    inside_func_signature = False

                    # check if the function has a body
                    if '{' in stripped_line:
                        inside_inlined_func_signature = True
                        brace_level = set_brace_level(brace_level, stripped_line)
                        # if brace level is back to 1, the function was defined in 1 line.
                        if brace_level == 1:
                            attrs = list(next_member_attrs)
                            next_member_attrs.clear()
                            inside_inlined_func_signature = False
                            func = BromaFunction.parse_multiline_signature_inlined(current_func_signature_text, [stripped_line.partition("{")[2].rpartition("}")[0]], class_name, attrs)
                            parts.append(func)
                        else:
                            current_inlined_func_signature_text.clear()
                            current_inlined_func_signature_text.append(line) # raw line, not stripped
                    else:
                        attrs = list(next_member_attrs)
                        next_member_attrs.clear()
                        func = BromaFunction.parse_multiline_signature(current_func_signature_text, class_name, attrs)
                        parts.append(func)

            # member
            elif brace_level == 1 and is_member(stripped_line):
                attrs = list(next_member_attrs)
                next_member_attrs.clear()

                if stripped_line.startswith("PAD"):
                    # a pad
                    broma_pad = BromaPad()
                    if '=' in stripped_line:
                        platform_pads = [x.strip() for x in stripped_line.partition('=')[2].rpartition(";")[0].strip().split(',')]
                        for pad in platform_pads:
                            validate(pad.count(" ") == 1, f"invalid platform pad: {pad}")
                            platform, offset = pad.split(" ")
                            offset = int(offset, 16)
                            broma_pad.platforms[platform] = offset

                    parts.append(broma_pad)
                else:
                    # an actual member
                    type, name = split_variable(stripped_line.rpartition(";")[0])
                    inline_comment = ''
                    if '//' in line:
                        inline_comment = line.partition('//')[2]

                    parts.append(BromaMember(type.strip(), name.strip(), attrs, inline_comment))

            # platform specific block OR function
            elif brace_level == 1:
                if stripped_line == '}':
                    brace_level -= 1
                    continue

                if not stripped_line:
                    continue

                is_ps_block = '{' in stripped_line and not '(' in stripped_line

                if is_ps_block: # platform specific block
                    # parse platforms
                    current_block_platforms = stripped_line.partition('{')[0].strip().split(",")

                    # set everything else
                    current_block_text.clear()
                    current_block_text.append(line) # raw line, not stripped
                    inside_ps_block = True
                    brace_level = set_brace_level(brace_level, stripped_line)

                else: # function
                    # first determine if it's inlined or not
                    is_inlined = '{' in stripped_line
                    is_multiline_signature = stripped_line.count('(') != stripped_line.count(')')

                    if is_multiline_signature: #
                        inside_func_signature = True
                        current_func_signature_text = line + "\n"
                        current_func_sig_brace_level = set_brace_level(current_func_sig_brace_level, stripped_line, True)
                    elif not is_inlined: # non inlined function
                        attrs = list(next_member_attrs)
                        next_member_attrs.clear()
                        func = BromaFunction.parse(stripped_line, class_name, attrs)
                        parts.append(func)
                    else: # inlined function
                        inside_inlined_func = True
                        brace_level = set_brace_level(brace_level, stripped_line)
                        # if brace level is back to 1, the function was defined in 1 line.
                        if brace_level == 1:
                            attrs = list(next_member_attrs)
                            next_member_attrs.clear()
                            inside_inlined_func = False
                            func = BromaFunction.parse_inlined([stripped_line], class_name, attrs)
                            parts.append(func)
                        else:
                            current_inline_text.clear()
                            current_inline_text.append(line) # raw line, not stripped

            # should be unreachable
            else:
                validate(False, f"unexpected state: brace level {brace_level}")

        global_validate(len(class_name) > 0, start_line + len(input.splitlines()), "class name was empty")
        return BromaClass(class_name, attributes, parts, bases)

    @classmethod
    def _parse_v2(cls, input: str, start_line: int) -> BromaClass:
        # TODO: unimpl
        reader = CharReader(input)
        class_attributes = []

        parts = []

        brace_level = 0

        # class definition starts with optional attributes.
        reader.skip_comments_and_whitespace()
        if reader.peek() == '[':
            attrstr = reader.read_until(']]', True)
            class_attributes = [x.strip() for x in attrstr.strip('[]').split(',')]

        # now, the class name and bases
        reader.skip_comments_and_whitespace()
        reader.skip_until('class ', True)
        class_name = reader.read_until(' ', True).strip()
        reader.skip_char() # skip colon
        reader.skip_comments_and_whitespace()
        class_bases = [x.strip() for x in reader.read_until('{').strip().split(",") if x.strip()]

        validate(class_name, "class name was empty")
        validate(reader.read_char() == '{', "did not find the opening brace")
        reader.skip_line()
        reader.skip_until_not_any('\n', True)

        brace_level = 1
        line_idx = start_line

        def validate(cond, message):
            # TODO figure out line index
            global_validate(cond, line_idx, message)

        while True:
            line_idx += 1

            line = reader.peek_line()
            stripped_line = strip_line(line)
            inline_comment = None

            # empty line
            if not line.strip():
                parts.append(BromaComment(None))
                reader.skip_line()
                continue

            # single line comment
            if stripped_line.startswith("//"):
                parts.append(BromaComment(stripped_line[2:]))
                reader.skip_line()
                continue

            # multiline comment, does not halt parsing
            if '/*' in stripped_line:
                line = reader.read_until('/*', False).strip()
                stripped_line = strip_line(line)
                inline_comment = reader.read_until('*/', True).strip()[2:-2].strip()



            # append inline comment if was parsed earlier
            if inline_comment:
                parts.append(BromaComment(inline_comment))

    def dump(self) -> str:
        out = ""

        if self.attributes:
            out += f"[[{', '.join(self.attributes)}]]\n"

        out += f"class {self.name} "

        if len(self.bases) > 0:
            out += f': {", ".join(self.bases)} '

        out += "{\n"
        first_member = True

        # dump everything
        indent_level = 4
        for part in self.parts:
            # put an empty line before first members
            if isinstance(part, (BromaPad, BromaMember)) and first_member:
                first_member = False
                # out += "\n"

            if isinstance(part, BromaFunction):
                dumped = part.dump()
                # print(f"dumped:\n{dumped}")
                lines = dumped.splitlines()
                lines = [' ' * indent_level + x for x in lines]
                out += '\n'.join(lines)
            elif isinstance(part, BromaPlatformBlock):
                out += part.code
            elif isinstance(part, BromaMember):
                out += indent_lines(part.dump(), indent_level)
            elif isinstance(part, BromaPad):
                out += indent_lines(part.dump(), indent_level)
            elif isinstance(part, BromaComment):
                dumped = part.dump()
                if dumped:
                    out += ' ' * indent_level + dumped

            out += "\n"

        out += "}"
        return out

    def find_function(self, name: str, arglist: list[str] | None) -> BromaFunction:
        for func in self.parts:
            if not isinstance(func, BromaFunction):
                continue

            if func.name != name:
                continue

            if arglist is None:
                return func

            # verify arguments
            if func.get_arg_types() == arglist:
                return func

        return None

    # Remove any comments, empty lines
    def strip(self):
        self.parts = [x for x in self.parts if isinstance(x, (BromaFunction, BromaMember, BromaPad))]

class BromaFunction:
    name: str
    inlined_body: str # from left brace to right brace
    attrs: list[str] # such as static, virtual, callback
    args: list[tuple[str, str]] = [] # [(type, name)]
    ret_type: str
    binds: dict[str, int | None] # None means inlined, int is an offset
    qualifier: str # such as const, &, &&, const&
    cpp_attrs: list[str] # [[attr]] attributes
    inline_comment: str = ""

    KNOWN_ATTRS = ["static", "virtual", "callback", "inline"]

    def __init__(self, name: str, inlined_body: str, attrs: list[str], args: list[tuple[str, str]], ret_type: str, binds: dict[str, int | None], qualifier: str, cpp_attrs: list[str], inline_comment: str = "") -> None:
        self.name = name
        self.inlined_body = inlined_body
        self.attrs = attrs
        self.args = args
        self.ret_type = ret_type
        self.binds = binds
        self.qualifier = qualifier
        self.cpp_attrs = cpp_attrs
        self.inline_comment = inline_comment

    @classmethod
    def parse(cls, line: str, class_name: str, cpp_attrs: list[str]) -> BromaFunction:
        inst = cls._parse_basic(line, class_name, cpp_attrs)
        return inst

    @classmethod
    def parse_inlined(cls, lines: list[str], class_name: str, cpp_attrs: list[str]) -> BromaFunction:
        inst = cls._parse_basic(lines[0], class_name, cpp_attrs)
        inlined_str = "\n".join(lines)
        brace_level = 0

        for char in inlined_str:
            if char == '{':
                brace_level += 1
            elif char == '}':
                brace_level -= 1

            if brace_level > 0 or (char == '}' and brace_level == 0):
                inst.inlined_body += char

        lines = inst.inlined_body.splitlines()
        # dedent by 1 level
        for n, line in enumerate(lines):
            if line.startswith("\t"):
                lines[n] = line[1:]
            elif line.startswith("    "):
                lines[n] = line[4:]

        inst.inlined_body = '\n'.join(lines)

        return inst

    @classmethod
    def parse_multiline_signature(cls, signature: str, class_name: str, cpp_attrs: list[str]) -> BromaFunction:
        # fuck your multiline
        signature = signature.replace('\n', '')
        return cls.parse(signature, class_name, cpp_attrs)

    @classmethod
    def parse_multiline_signature_inlined(cls, signature: str, body: list[str], class_name: str, cpp_attrs: list[str]) -> BromaFunction:
        signature = signature.replace('\n', '')
        return cls.parse_inlined([signature] + body, class_name, cpp_attrs)

    @classmethod
    def _parse_basic(cls, line: str, class_name: str, cpp_attrs: list[str]) -> BromaFunction:
        if "::" in class_name:
            unq_class_name = class_name.rpartition("::")[2]
        else:
            unq_class_name = class_name

        # parse attributes
        attrs = []

        fn_name = ""

        while True:
            found_attrs = False

            for attr in cls.KNOWN_ATTRS:
                if line.startswith(attr):
                    attrs.append(attr)
                    line = line[len(attr) + 1:]
                    found_attrs = True

            if not found_attrs:
                break

        # check for ctor/dtor
        if line.startswith("~"):
            fn_name = f"~{unq_class_name}"
        elif line.startswith(f"{unq_class_name}("):
            fn_name = unq_class_name
        else:
            # anything else
            fn_name = line.partition("(")[0]
            if " " in fn_name:
                fn_name = fn_name.rpartition(" ")[2]
            if "*" in fn_name:
                fn_name = fn_name.rpartition("*")[2].strip()

        ret_type = line.partition(fn_name)[0].strip()
        arglist = [split_variable(x.strip()) for x in line.partition(fn_name)[2].partition("(")[2].partition(")")[0].split(",") if x.strip()]

        past_args = line.partition(")")[2]
        if '=' in past_args:
            qualifier, _, ending = line.partition(")")[2].partition("=")
            ending = ending.partition(";")[0].partition("{")[0]
            binds_list = [x.strip() for x in ending.strip('{;').strip().split(",") if x.strip()]
        else:
            # no binds
            qualifier = past_args.partition(";")[0].partition("{")[0]
            binds_list = []

        inline_comment = ""
        if '//' in past_args:
            inline_comment = past_args.partition("//")[2]

        qualifier = qualifier.strip()

        binds = {}

        for bind in binds_list:
            assert bind.count(' ') == 1, bind
            platform, offset = bind.split(' ')
            if offset == 'inline':
                binds[platform] = None
            elif offset.startswith("0x"):
                try:
                    off = int(offset, 16)
                    binds[platform] = off
                except Exception as e:
                    print(f"WARN: failed to parse platform bind line: {e} (offset was {offset})")
                    print(f"Line: {line}")

        return cls(
            fn_name, "", attrs, arglist, ret_type, binds, qualifier, cpp_attrs, inline_comment
        )

    def get_arg_types(self) -> list[str]:
        return [x[0] for x in self.args]

    def dump(self) -> str:
        out = ""
        if self.cpp_attrs:
            out += f"[[{', '.join(self.cpp_attrs)}]]\n"

        if self.attrs:
            out = f"{' '.join(self.attrs)} "

        if self.ret_type:
            out += f"{self.ret_type} "

        out += self.name
        arg_list = []
        for type, name in self.args:
            if not name:
                arg_list.append(type)
            else:
                arg_list.append(f'{type} {name}')

        arg_list = ', '.join(arg_list)
        out += f"({arg_list})"

        if self.qualifier:
            out += f" {self.qualifier}"

        # indent inlined body
        inlined_body = ""
        if self.inlined_body:
            lines = self.inlined_body.splitlines()
            indent_level = 0

            out_lines = []
            for line in lines:
                new_indent_level = set_brace_level(indent_level, line)
                if new_indent_level < indent_level:
                    indent_level = new_indent_level

                out_lines.append(line)
                indent_level = new_indent_level

            inlined_body = '\n'.join(out_lines)

        if not self.binds:
            if inlined_body:
                out += " " + inlined_body
            else:
                out += ";"
            return out

        # add binds
        out += " = "
        bind_strings = []
        for bind in self.binds:
            if self.binds[bind] is None:
                bind_strings.append(f"{bind} inline")
            else:
                bind_strings.append(f"{bind} {hex(self.binds[bind])}")

        out += ", ".join(bind_strings)

        if not self.inlined_body:
            out += ";"

            if self.inline_comment:
                out += f" //{self.inline_comment.rstrip()}"

            return out

        # add inlined body
        out += " " + inlined_body

        return out

class Broma:
    raw_lines: list[str] # raw lines as they were in the input
    classes: list[BromaClass]
    preamble: str = ""

    def __init__(self, content: str) -> None:
        self.raw_lines = content.splitlines()
        self.preamble, start_of_classes = self.parse_preamble()
        self.classes = self.parse_classes(start_of_classes)

    def preprocess(self, content: str) -> list[str]:
        return [x.strip() for x in content.splitlines()]

    def parse_classes(self, start_of_classes: int) -> list[BromaClass]:
        classes: list[tuple[str, int]] = [] # (class, first line)

        current_class_str = ""
        current_class_start = 0
        brace_level = 0

        # first parse each class into a separate string, then call BromaClass.parse() on them all
        for line_idx, raw_line in enumerate(self.raw_lines):
            # skip preamble
            if line_idx < start_of_classes:
                continue

            stripped_line = strip_line(raw_line)

            # if in global ns and empty line / comment, skip it
            if brace_level == 0 and not stripped_line:
                continue

            was_empty = current_class_str == ""
            current_class_str += raw_line + "\n"

            if was_empty and current_class_str:
                current_class_start = line_idx

            old_brace_level = brace_level
            brace_level = set_brace_level(brace_level, stripped_line)

            if brace_level < old_brace_level and brace_level == 0:
                # end of the class
                classes.append((current_class_str, current_class_start))
                current_class_str = ""

        out = []

        # now, parse each class separately
        for (data, start_line) in classes:
            c = BromaClass.parse(data, start_line)
            out.append(c)

        return out
        # # attributes
        # if match := re.match(r"\[\[(.*)\]\]", stripped_line):
        #     validate(brace_level == 0, "attribute field not in the global namespace")

        #     current_attrs += [x.strip() for x in match.group(1).split(",")]

        # brace_level = 0
        # current_class = BromaClass()
        # current_inline = []

        # for line_idx, line in enumerate(self.raw_lines):
        #     # comment or empty line can be skipped
        #     if line.startswith("//") or not line:
        #         continue

        #     if brace_level == 0:
        #         # attributes
        #         if match := re.match(r"\[\[(.*)\]\]", line):
        #             current_class.attributes = [x.strip() for x in match.group(1).split(",")]

        #         # class name
        #         if match := re.match(r"class[\s]+([a-zA-Z0-9_]+)[\s]*:?[ ]*([a-zA-Z0-9_:, ]*)[\s]*{", line):
        #             current_class.name = match.group(1)
        #             bases_str = match.group(2)
        #             if bases_str:
        #                 current_class.bases = [x.strip() for x in bases_str.split(",")]

        #             brace_level = set_brace_level(brace_level, line)
        #             # print(f"Start class {current_class.name}")

        #             assert brace_level == 1

        #     # inside of a class, but not a function
        #     elif brace_level == 1 and not self.is_member(line):
        #         old_brace_level = brace_level
        #         has_inline = False

        #         if '{' in line or '}' in line:
        #             brace_level = set_brace_level(brace_level, line)

        #         if brace_level > old_brace_level or '{' in line:
        #             has_inline = True
        #         elif brace_level < old_brace_level:
        #             # end of the class
        #             assert len(current_class.name) > 0
        #             # print(f"End class {current_class.name}")

        #             current_class.struct.process()
        #             out.append(current_class)
        #             current_class = BromaClass()
        #             continue

        #         # no inline definition, just parse the function
        #         if not has_inline:
        #             func = BromaFunction.parse(line, current_class.name)
        #             current_class.functions.append(func)
        #             continue

        #         # inline function
        #         current_inline.clear()
        #         current_inline.append(line)

        #         # if this is a one line inlined function, add it immediately
        #         if brace_level == old_brace_level:
        #             func = BromaFunction.parse_inlined(current_inline, current_class.name)
        #             current_class.functions.append(func)
        #             continue

        #     # inside of an inlined function
        #     elif brace_level > 1:
        #         brace_level = set_brace_level(brace_level, line)

        #         current_inline.append(line)
        #         if brace_level == 1:
        #             # end of inlined function
        #             func = BromaFunction.parse_inlined(current_inline, current_class.name)
        #             current_class.functions.append(func)
        #             continue

        #     # a member
        #     elif brace_level == 1:
        #         if line.startswith("PAD"):
        #             # a pad
        #             broma_pad = BromaPad()
        #             if '=' in line:
        #                 platform_pads = [x.strip() for x in line.partition('=')[2].rpartition(";")[0].strip().split(',')]
        #                 for pad in platform_pads:
        #                     assert pad.count(" ") == 1
        #                     platform, offset = pad.split(" ")
        #                     offset = int(offset, 16)
        #                     broma_pad.platforms[platform] = offset

        #             current_class.struct.raw_members.append(broma_pad)
        #         else:
        #             # an actual member
        #             type, _, name = line.rpartition(";")[0].rpartition(" ")
        #             while name.startswith("*"):
        #                 name = name[1:]
        #                 type = type + "*"

        #             current_class.struct.raw_members.append(BromaMember(type, name))

        # return out

    # simply iterate over the lines until the first line that is not empty and not a comment is found
    def parse_preamble(self) -> tuple[str, int]:
        pr = ""

        inside_ml_comment = False

        total_lines = 0

        for line in self.raw_lines:
            stripped = strip_line(line)

            if '/*' in stripped:
                inside_ml_comment = True
                if '*/' in stripped and stripped.rfind('*/') > stripped.rfind('/*'):
                    inside_ml_comment = False

                pr += line + "\n"
            elif inside_ml_comment:
                if '*/' in line:
                    inside_ml_comment = False
                pr += line + "\n"
            elif stripped: # non empty line that is not a comment
                return (pr, total_lines)
            else:
                pr += line + "\n"


            total_lines += 1

    def find_class(self, name: str) -> BromaClass:
        for class_ in self.classes:
            if class_.name == name:
                return class_

        # now look for unqalified matches
        for class_ in self.classes:
            cname = class_.name
            if '::' in cname:
                cname = cname.rpartition('::')[2]

            if '::' in name:
                name = name.rpartition('::')[2]

            if cname == name:
                return class_

        return None

    def dump(self) -> str:
        out = self.preamble

        for cls in self.classes:
            out += cls.dump()
            out += "\n\n"

        return out

def parse(path: Path | str) -> Broma:
    if Path(path).exists():
        return Broma(Path(path).read_text(encoding='utf-8'))
    else:
        return Broma(path) # assume it's a string

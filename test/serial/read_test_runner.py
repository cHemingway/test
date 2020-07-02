import json
import re
import sys
import argparse
from typing import List

import pcpp
from elftools.elf.descriptions import describe_reloc_type
from elftools.elf.relocation import RelocationSection
from elftools.elf.sections import SymbolTableSection

from metal.serial import Engine, read_symbols
from subprocess import PIPE, Popen, check_output

from metal.serial.elfreader import ELFReader
from metal.serial.generate import generate
from metal.serial.preprocessor import preprocess_compile_unit, MacroExpansion

parser = argparse.ArgumentParser()

parser.add_argument('binary',           help='The binary that runs on target')
parser.add_argument('-S', '--source-dir',  required=True, help='The root of the source directory')
parser.add_argument('-I', '--include', nargs='+', help="Include folders for the preprocessor", default=[])
parser.add_argument('-D', '--define', nargs='+', help="Defines for the preprocessor", default=[])

args = parser.parse_args()

serial_info = generate(args.binary, args.define, args.include)

p = Popen(args.binary, stdin=PIPE, stdout=PIPE, close_fds=True)
engine = Engine(input=p.stdout, output=p.stdin, serial_info=serial_info)

assert engine.init_marker.file.endswith('read.c')
assert engine.init_marker.line == 22

assert engine.read_byte() == b'a'
assert engine.read_int() == 42
assert engine.read_string() == "test-string"

main_ptr = engine.read_int() - engine.base_pointer
assert [sym.address for sym in serial_info.symbols if sym.name == 'main'][0] == main_ptr

assert int.from_bytes(engine.read_memory(), engine.endianness) == 42
assert engine.read_int() == 1234

assert engine.run() == 42
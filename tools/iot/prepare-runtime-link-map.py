"""Add map/cref to the native RC link recipe's actual `all` target."""
import argparse
from pathlib import Path
import re


def prepare(makefile, output):
    if makefile.is_symlink() or not makefile.is_file() or output.exists() or output.is_symlink():
        raise ValueError('Regular RC Makefile and new map destination required')
    text = makefile.read_text()
    recipe = ('all: $(OBJS) Makefile\n'
              '\t$(CC) -o $(EXEC) $(OBJS) $(LDFLAGS)\n'
              '\t$(STRIP) $(EXEC)')
    if text.count('EXEC = rc\n') != 1 or text.count(recipe) != 1 or '-Map,' in text:
        raise ValueError('Native RC all-target link recipe changed or already prepared')
    destination = str(output.resolve())
    if not re.fullmatch(r'[/A-Za-z0-9_.:-]+', destination):
        raise ValueError('Make/linker-safe absolute map destination required')
    makefile.write_text(text + '\nall: override LDFLAGS += -Wl,-Map,' + destination + ',--cref\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('makefile', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    prepare(args.makefile, args.output)

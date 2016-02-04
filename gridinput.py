
# http://tools.qhex.org/
#
# Reads a grid puzzle from stdin.
# Defines puz, height, width, and convenience functions.

import sys

puz = sys.stdin.read().replace('\t',' ')
if '`' not in puz: puz = puz.replace('_','`')
if '`' not in puz: puz = puz.replace('.','`')
puz = map(lambda row: filter(bool, row.split(' ')),
          filter(bool, puz.split('\n')))

if all(len(row) == 1 for row in puz):  # parse without spaces
    puz = map(lambda row: list(row[0].strip()), puz)

height = len(puz)
width = len(puz[0])
for row in puz:
    if len(row) != width:
        print 'Error: array is not rectangular at row:\n'
        print ' '.join(row)
        sys.exit()

def p(x):
    widths = [0] * max(map(len, x))
    for row in x:
        for c, val in enumerate(row):
            widths[c] = max(widths[c], len(str(val)))
    for row in x:
        print ' '.join(map(lambda val, width: str(val).rjust(width),
                           row, widths))

def nrange(*dim_sizes):
    """Returns an iterator of all coordinates within the given dimensions."""
    if len(dim_sizes) == 1:
        for i in range(dim_sizes[0]):
            yield (i,)
        return
    for i in range(dim_sizes[0]):
        for rest in apply(nrange, dim_sizes[1:]):
            yield (i,) + rest

def tmap(f, *args):
    return map(lambda *args1: map(f, *args1), *args)

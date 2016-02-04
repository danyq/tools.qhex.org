#!/usr/bin/python -u
#
# http://tools.qhex.org/

from claspy import *
import sys

puz = sys.stdin.read().strip()
puz = '\n'.join(map(lambda line: line.strip(), puz.split('\n')))
puz = puz.split('\n\n')
across = puz[0]
down = puz[1]

across = map(lambda line: map(int, filter(bool, line.split(' '))),
             filter(bool, across.split('\n')))
down = map(lambda line: map(int, filter(bool, line.split(' '))),
           filter(bool, down.split('\n')))

width = len(down)
height = len(across)
set_max_val(max(width, height))

grid = [[BoolVar() for c in range(width)] for r in range(height)]

def cumsum(input):
    x = 0
    output = []
    for i in input:
        x += i
        output.append(x)
    return output

def check(vals, row):
    """vals: the clue numbers.  row: list of BoolVars."""
    cum_count = IntVar(0)  # number of filled cells so far
    prev_cell = BoolVar(False)
    prev_group_end = BoolVar(False)
    for cell in row:
        cum_count += cell
        # whether the cumulative count matches the end of a group.
        group_end = reduce(lambda a,b: a|b,
                           map(lambda x: cum_count == int(x), cumsum(vals)))
        # if the prev cell is filled and current cell is not, this
        # must be a group end.
        require(cond(prev_cell & ~cell, group_end, True))
        # if both prev and current cells are filled, this must not
        # have been a group end.
        require(cond(prev_cell & cell, ~prev_group_end, True))
        prev_cell = cell
        prev_group_end = group_end
    # the total sum must match.
    require(cum_count == int(sum(vals)))

for r in range(height):
    check(across[r], grid[r])
for c in range(width):
    check(down[c], [grid[r][c] for r in range(height)])

soln_count = 0
while solve():
    soln_count += 1
    print 'Solution %d:' % soln_count
    for row in grid:
        print ' '.join(map(lambda x: '#' if x.value() else '`', row))
    print
    if soln_count >= 10:
        print 'Too many solutions...'
        break
    print 'Checking for other solutions'
    x = BoolVar(True)
    for r in range(height):
        for c in range(width):
            x = x & (grid[r][c] == grid[r][c].value())
    require(~x)

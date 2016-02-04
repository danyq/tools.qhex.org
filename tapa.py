#!/usr/bin/python -u
#
# http://tools.qhex.org/

from claspy import *
from gridinput import *

puz = tmap(lambda x: x.split(','), puz)

grid = [[BoolVar() for c in range(width)] for r in range(height)]

def cumsum(it):
    total = 0
    for x in it:
        total += x
        yield total

def check(vals, row):
    """vals: the clue numbers.  row: list of BoolVars."""
    cum_count = IntVar(0)  # number of filled cells so far
    prev_cell = BoolVar(False)
    prev_group_end = BoolVar(False)
    result = BoolVar(True)
    for cell in row:
        cum_count += cell
        # whether the cumulative count matches the end of a group.
        group_end = reduce(lambda a,b: a|b,
                           map(lambda x: cum_count == int(x), cumsum(vals)))
        # if the prev cell is filled and current cell is not, this
        # must be a group end.
        result = result & (cond(prev_cell & ~cell, group_end, True))
        # if both prev and current cells are filled, this must not
        # have been a group end.
        result = result & (cond(prev_cell & cell, ~prev_group_end, True))
        prev_cell = cell
        prev_group_end = group_end
    # the total sum must match.
    result = result & (cum_count == int(sum(vals)))
    return result

for r,c in nrange(height, width):
    if puz[r][c] == ['`']: continue
    require(~grid[r][c])
    valid = BoolVar(False)
    vars = []
    for dr,dc in [(-1,-1),(-1,0),(-1,1),(0,1),(1,1),(1,0),(1,-1),(0,-1)]:
        if r + dr < 0 or r + dr >= height:
            vars.append(BoolVar(False))
            continue
        if c + dc < 0 or c + dc >= width:
            vars.append(BoolVar(False))
            continue
        vars.append(grid[r+dr][c+dc])
    for i in range(8):
        valid = valid | (check(map(int, puz[r][c]), vars[i:] + vars[:i]) & ~vars[i])
    require(valid)

# require connectivity for filled cells
source = MultiVar(*nrange(height,width))
c_grid = [[Atom() for c in range(width)] for r in range(height)]
for r,c in nrange(height, width):
    c_grid[r][c].prove_if(source == (r,c))
    if c > 0: c_grid[r][c].prove_if(grid[r][c-1] & c_grid[r][c-1])
    if c < width-1: c_grid[r][c].prove_if(grid[r][c+1] & c_grid[r][c+1])
    if r > 0: c_grid[r][c].prove_if(grid[r-1][c] & c_grid[r-1][c])
    if r < height-1: c_grid[r][c].prove_if(grid[r+1][c] & c_grid[r+1][c])
    require(cond(grid[r][c], c_grid[r][c], True))

# require no group of four filled cells
for r,c in nrange(height-1, width-1):
    require(~grid[r][c] | ~grid[r][c+1] | ~grid[r+1][c] | ~grid[r+1][c+1])

soln_count = 0
while solve():
    soln_count += 1
    print 'Solution %d:' % soln_count
    p(tmap(lambda g,p: '#' if g.value() else (p[0] if len(p) == 1 else 'x'), grid, puz))
    print
    if soln_count >= 10:
        print 'Too many solutions...'
        break
    print 'Checking for other solutions'
    x = BoolVar(True)
    for r,c in nrange(height, width):
        x = x & (grid[r][c] == grid[r][c].value())
    require(~x)

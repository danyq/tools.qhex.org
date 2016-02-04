#!/usr/bin/python -u
#
# http://tools.qhex.org/

from claspy import *
from gridinput import *

fill_grid = [[BoolVar() for c in range(width)] for r in range(height)]

# constrain unique numbers on each row
for r in range(height):
    for x in set(puz[r]):  # each possible number
        if sum([puz[r][c] == x for c in range(width)]) > 1:  # repeated
            cs = [c for c in range(width) if puz[r][c] == x]
            require(at_most(1, [~fill_grid[r][c] for c in cs]))

# constrain unique numbers on each col
for c in range(width):
    for x in set([row[c] for row in puz]):  # each possible number
        if sum([puz[r][c] == x for r in range(height)]) > 1:  # repeated
            rs = [r for r in range(height) if puz[r][c] == x]
            require(at_most(1, [~fill_grid[r][c] for r in rs]))

# vertically adjacent cannot be filled
for r,c in nrange(height-1,width):
    require(~(fill_grid[r][c] & fill_grid[r+1][c]))

# horizontally adjacent cannot be filled
for r,c in nrange(height,width-1):
    require(~(fill_grid[r][c] & fill_grid[r][c+1]))

## constrain connectivity
conn_grid = [[Atom() for c in range(width)] for r in range(height)]
# the first two cells are proven (one might be filled in)
conn_grid[0][0].prove_if(True)
conn_grid[0][1].prove_if(True)
for r,c in nrange(height, width):
    for r1,c1 in [(r,c-1),(r,c+1),(r-1,c),(r+1,c)]:
        if r1 >= 0 and r1 < height and c1 >= 0 and c1 < width:
            conn_grid[r][c].prove_if(conn_grid[r1][c1] & ~fill_grid[r1][c1])
    require(conn_grid[r][c])

soln_count = 0
while solve():
    soln_count += 1
    print 'Solution %d:' % soln_count
    p(tmap(lambda f,p: '##' if f.value() else p, fill_grid, puz))
    print
    if soln_count >= 10:
        print 'Too many solutions...'
        break
    print 'Checking for other solutions'
    x = BoolVar(True)
    for r,c in nrange(height, width):
        x = x & (fill_grid[r][c] == fill_grid[r][c].value())
    require(~x)

#!/usr/bin/python -u
#
# http://tools.qhex.org/

from claspy import *
from gridinput import *

grid = [[BoolVar() for c in range(width)] for r in range(height)]

for r,c in nrange(height, width):
    if puz[r][c] == '`': continue
    vars = []  # collect all the neighborhood variables
    for dr,dc in nrange(3,3):
        r1,c1 = r+dr-1,c+dc-1
        if r1 >= 0 and r1 < height and c1 >= 0 and c1 < width:
            vars.append(grid[r1][c1])
    require(sum_bools(int(puz[r][c]), vars))

soln_count = 0
while solve():
    soln_count += 1
    print 'Solution %d:' % soln_count
    p(tmap(lambda x: '#' if x.value() else '`', grid))
    print
    if soln_count >= 10:
        print 'Too many solutions...'
        break
    print 'Checking for other solutions'
    x = BoolVar(True)
    for r,c in nrange(height, width):
        x = x & (grid[r][c] == grid[r][c].value())
    require(~x)

#!/usr/bin/python -u
#
# http://tools.qhex.org/

from claspy import *
from gridinput import *

grid = [[BoolVar() for c in range(width)] for r in range(height)]

for r,c in nrange(height, width):
    if puz[r][c] not in ('#', '`'):
        sys.exit('unrecognized character: %s' % puz[r][c])

for r,c in nrange(height, width):
    result = BoolVar(puz[r][c] != '`')
    for r1,c1 in ((r,c),(r,c-1),(r,c+1),(r-1,c),(r+1,c)):
        if r1 >= 0 and r1 < height and c1 >= 0 and c1 < width:
            result ^= grid[r1][c1]
    require(~result)

soln_count = 0
while solve():
    soln_count += 1
    print 'Solution %d:' % soln_count
    p(tmap(lambda g,p: '#' if g.value() else '`', grid, puz))
    print
    if soln_count >= 10:
        print 'Too many solutions...'
        break
    print 'Checking for other solutions'
    x = BoolVar(True)
    for r,c in nrange(height, width):
        x = x & (grid[r][c] == grid[r][c].value())
    require(~x)

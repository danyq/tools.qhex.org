#!/usr/bin/python -u
#
# http://tools.qhex.org/

from claspy import *
from gridinput import *

vertical = puz[-1][:-1]
horizontal = [row[-1] for row in puz[:-1]]

if not any(x in 'o><^v' for x in reduce(lambda a,b: a+b, puz)):
    print 'No recognized symbols in thermometers puzzle.'
    sys.exit()

if sum(x != '`' for x in vertical+horizontal) < (width+height-2)/2:
    print 'Not enough given sums for thermometers puzzle of size %d x %d.' % (width, height)
    sys.exit()

puz = [row[:-1] for row in puz[:-1]]
height -= 1
width -= 1

grid = [[BoolVar() for c in range(width)] for r in range(height)]

for r in range(height):
    if horizontal[r] != '`':
        require(sum_bools(int(horizontal[r]), grid[r]))

for c in range(width):
    if vertical[c] != '`':
        require(sum_bools(int(vertical[c]), [grid[r][c] for r in range(height)]))

for r,c in nrange(height, width-1):
    if puz[r][c] in 'o>' and puz[r][c+1] == '>':
        require(~(~grid[r][c] & grid[r][c+1]))
    if puz[r][c] == '<' and puz[r][c+1] in '<o':
        require(~(grid[r][c] & ~grid[r][c+1]))
for r,c in nrange(height-1, width):
    if puz[r][c] in 'ov' and puz[r+1][c] == 'v':
        require(~(~grid[r][c] & grid[r+1][c]))
    if puz[r][c] == '^' and puz[r+1][c] in '^o':
        require(~(grid[r][c] & ~grid[r+1][c]))

soln_count = 0
while solve():
    soln_count += 1
    print 'Solution %d:' % soln_count
    p(tmap(lambda g,p: p if g.value() else '`', grid, puz))
    print
    if soln_count >= 10:
        print 'Too many solutions...'
        break
    print 'Checking for other solutions'
    x = BoolVar(True)
    for r,c in nrange(height, width):
        x = x & (grid[r][c] == grid[r][c].value())
    require(~x)

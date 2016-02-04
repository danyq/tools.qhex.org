#!/usr/bin/python -u
#
# http://tools.qhex.org/

from claspy import *
from gridinput import *
from copy import deepcopy

if sum('\\' in x and x != '\\'
       for x in reduce(lambda a,b: a+b, puz)) < (width+height)/2:
    print 'Not enough givens for kakuro of size %d x %d.' % (width,height)
    sys.exit()

grid = deepcopy(puz)
for r,c in nrange(height, width):
    if puz[r][c] == '`':
        grid[r][c] = IntVar(1,9)

for r,c in nrange(height, width):
    if '\\' not in puz[r][c]: continue
    down_val, right_val = puz[r][c].split('\\')
    if right_val:
        cells = []
        c1 = c+1
        while c1 < width and puz[r][c1] == '`':
            cells.append(grid[r][c1])
            c1 += 1
        require(sum_vars(cells) == int(right_val))
        require_all_diff(cells)
    if down_val:
        cells = []
        r1 = r+1
        while r1 < height and puz[r1][c] == '`':
            cells.append(grid[r1][c])
            r1 += 1
        require(sum_vars(cells) == int(down_val))
        require_all_diff(cells)

soln_count = 0
while solve():
    soln_count += 1
    print 'Solution %d:' % soln_count
    widths = [max([len(str(row[c])) for row in grid])
              for c in range(height)]
    for row in grid:
        print ' '.join(map(lambda val, width: str(val).center(width),
                           row, widths))
    print
    if soln_count >= 10:
        print 'Too many solutions...'
        break
    print 'Checking for other solutions'
    x = BoolVar(True)
    for r,c in nrange(height, width):
        if puz[r][c] == '`':
            x = x & (grid[r][c] == grid[r][c].value())
    require(~x)

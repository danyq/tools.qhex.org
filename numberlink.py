#!/usr/bin/python -u
#
# http://tools.qhex.org/

from claspy import *
from gridinput import *

# for numbers, this is faster
#num_links = max(map(lambda x: 0 if x == '`' else int(x),
#                    reduce(lambda a,b: a+b, puz)))
#grid = [[IntVar(1,num_links) if puz[r][c] == '`' else IntVar(int(puz[r][c]))
#         for c in range(width)] for r in range(height)]

vals = set(reduce(lambda a,b: a+b, puz)) - set(['`'])
grid = tmap(lambda x: MultiVar(*vals) if x == '`' else MultiVar(x), puz)

for r,c in nrange(height, width):
    same_neighbors = []
    for r1,c1 in [(r,c-1), (r,c+1), (r-1,c), (r+1,c)]:
        if r1 >= 0 and c1 >= 0 and r1 < height and c1 < width:
            same_neighbors.append(grid[r][c] == grid[r1][c1])
    if puz[r][c] == '`':
        require(sum_bools(2, same_neighbors))
    else:
        require(sum_bools(1, same_neighbors))

soln_count = 0
while solve():
    soln_count += 1
    print 'Solution %d:' % soln_count
    p(grid)
    print
    if soln_count >= 10:
        print 'Too many solutions...'
        break
    print 'Checking for other solutions'
    x = BoolVar(True)
    for r,c in nrange(height, width):
        x = x & (grid[r][c] == grid[r][c].value())
    require(~x)

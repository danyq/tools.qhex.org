#!/usr/bin/python -u
#
# http://tools.qhex.org/

from claspy import *
from gridinput import *

assert height == 9
assert width == 9

vals = set(reduce(lambda a,b: a+b, puz)) - set(['`'])
if len(vals) > 9:
    print 'Too many distinct symbols:', ' '.join(list(vals))
    sys.exit()
for i in range(1,10):
    if len(vals) < 9:
        vals.add(str(i))
grid = tmap(lambda x: MultiVar(*vals) if x == '`' else MultiVar(x), puz)

# for regular sudoku, this is faster
# grid = tmap(lambda x: IntVar(1,9) if x == '`' else IntVar(int(x)), puz)

for r in range(9):
    require_all_diff(grid[r])
for c in range(9):
    require_all_diff([grid[r][c] for r in range(9)])
for r in range(0,9,3):
    for c in range(0,9,3):
        require_all_diff([grid[r+i][c+j] for (i,j) in nrange(3,3)])

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
    for r,c in nrange(9,9):
        x = x & (grid[r][c] == grid[r][c].value())
    require(~x)

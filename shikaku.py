#!/usr/bin/python -u
#
# http://tools.qhex.org/

from claspy import *
from gridinput import *

max_val = max(map(lambda x: 0 if x == '`' else int(x),
                  reduce(lambda a,b: a+b, puz)))
set_max_val(width ** 3)

groups = sum(map(lambda x: x != '`', reduce(lambda a,b: a+b, puz)))
group = [[IntVar(0,groups-1) for c in range(width)] for r in range(height)]
print groups, "groups"
group_id = 0
for r,c in nrange(height, width):
    if puz[r][c] == '`': continue
    require(group[r][c] == group_id)
    # all rectangles
    rect_ok = BoolVar(False)
    for r1,c1,r2,c2 in nrange(height, width, height, width):
        if r2 < r1 or c2 < c1: continue
        if r1 > r or c1 > c: continue
        if r2 < r or c2 < c: continue
        if (r2 - r1 + 1) * (c2 - c1 + 1) != int(puz[r][c]): continue
        group_valid = BoolVar(True)
        # all cells in rectangle
        for r3,c3 in nrange(height, width):
            if r3 >= r1 and r3 <= r2 and c3 >= c1 and c3 <= c2:
                group_valid = group_valid & (group[r3][c3] == group_id)
            else:
                group_valid = group_valid & (group[r3][c3] != group_id)
        rect_ok = rect_ok | group_valid
    require(rect_ok, str((r,c)))
    group_id += 1

soln_count = 0
while solve():
    soln_count += 1
    print 'Solution %d:' % soln_count
    x = [['' for c in range(width*2-1)] for r in range(height*2-1)]
    for r,c in nrange(height, width):
        x[r*2][c*2] = puz[r][c]
    for r,c in nrange(height-1, width):
        if group[r][c].value() != group[r+1][c].value():
            x[r*2+1][c*2] = '--'
            if c < width - 1: x[r*2+1][c*2+1] = '--'
    for r,c in nrange(height, width-1):
        if group[r][c].value() != group[r][c+1].value():
            x[r*2][c*2+1] = x[r*2][c*2+1][:1] + '|'
            if r < height - 1: x[r*2+1][c*2+1] = x[r*2+1][c*2+1][:1] + '|'
    for row in x:
        print ''.join(map(lambda a: a.rjust(2), row))
    print
    if soln_count >= 10:
        print 'Too many solutions...'
        break
    print 'Checking for other solutions'
    x = BoolVar(True)
    for r,c in nrange(height, width):
        x = x & (group[r][c] == group[r][c].value())
    require(~x)

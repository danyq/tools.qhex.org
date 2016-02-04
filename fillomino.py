#!/usr/bin/python -u
#
# http://tools.qhex.org/

from claspy import *
from gridinput import *

vals = map(lambda x: 0 if x == '`' else int(x),
           reduce(lambda a,b: a+b, puz))
max_val = max(vals)

if sum(vals) < width*height:
    print 'Not enough givens for a fillomino of size %d x %d.' % (width, height)
    sys.exit()

set_max_val(width*height)
grid = tmap(lambda x: IntVar(1,max_val) if x == '`' else IntVar(int(x)), puz)

# create a flow field
flow = [[MultiVar('^','v','>','<','.') for c in range(width)] for r in range(height)]
flow_c = [[Atom() for c in range(width)] for r in range(height)]
for r,c in nrange(height, width):
    # flow field terminates at a '.'
    flow_c[r][c].prove_if(flow[r][c] == '.')
    if r > 0:
        flow_c[r][c].prove_if((flow[r][c] == '^') & flow_c[r-1][c] & (grid[r][c] == grid[r-1][c]))
    if r < height-1:
        flow_c[r][c].prove_if((flow[r][c] == 'v') & flow_c[r+1][c] & (grid[r][c] == grid[r+1][c]))
    if c > 0:
        flow_c[r][c].prove_if((flow[r][c] == '<') & flow_c[r][c-1] & (grid[r][c] == grid[r][c-1]))
    if c < width-1:
        flow_c[r][c].prove_if((flow[r][c] == '>') & flow_c[r][c+1] & (grid[r][c] == grid[r][c+1]))
    require(flow_c[r][c])

# count cells that are upstream in the flow
upstream = [[IntVar(0,max_val) for c in range(width)] for r in range(height)]
for r,c in nrange(height, width):
    upstream_count = IntVar(0)
    if r > 0:        upstream_count += cond(flow[r-1][c] == 'v', upstream[r-1][c], 0)
    if r < height-1: upstream_count += cond(flow[r+1][c] == '^', upstream[r+1][c], 0)
    if c > 0:        upstream_count += cond(flow[r][c-1] == '>', upstream[r][c-1], 0)
    if c < width-1:  upstream_count += cond(flow[r][c+1] == '<', upstream[r][c+1], 0)
    require(upstream[r][c] == upstream_count + 1)
    require(cond(flow[r][c] == '.', upstream[r][c] == grid[r][c], True))

# require no two groups to come in contact.
# each group is identified by the cell number of the flow field target (row*width + col).
group = [[IntVar(0,width*height) for c in range(width)] for r in range(height)]
for r,c in nrange(height, width):
    require(cond(flow[r][c] == '.', group[r][c] == r*width + c, True))
# require vertically adjacent to have the same group
for r,c in nrange(height-1, width):
    require(cond(grid[r][c] == grid[r+1][c], group[r][c] == group[r+1][c], True))
# require horizontally adjacent to have the same group
for r,c in nrange(height, width-1):
    require(cond(grid[r][c] == grid[r][c+1], group[r][c] == group[r][c+1], True))

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

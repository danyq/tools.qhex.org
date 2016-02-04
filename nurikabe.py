#!/usr/bin/python -u
#
# http://tools.qhex.org/

from claspy import *
from gridinput import *

max_val = max(map(lambda x: 0 if x == '`' else int(x),
                  reduce(lambda a,b: a+b, puz)))

set_max_val(width*height)
grid = tmap(lambda x: BoolVar() if x == '`' else BoolVar(False), puz)

# create a flow field in empty cells towards each number
flow = [[MultiVar('^','v','>','<','.') for c in range(width)] for r in range(height)]
flow_c = [[Atom() for c in range(width)] for r in range(height)]
for r,c in nrange(height, width):
    if puz[r][c] != '`':  # source
        require(flow[r][c] == '.')
        flow_c[r][c].prove_if(True)
        continue
    require((flow[r][c] == '.') == grid[r][c])
    if r > 0:        flow_c[r][c].prove_if((flow[r][c] == '^') & ~grid[r-1][c] & flow_c[r-1][c])
    if r < height-1: flow_c[r][c].prove_if((flow[r][c] == 'v') & ~grid[r+1][c] & flow_c[r+1][c])
    if c > 0:        flow_c[r][c].prove_if((flow[r][c] == '<') & ~grid[r][c-1] & flow_c[r][c-1])
    if c < width-1:  flow_c[r][c].prove_if((flow[r][c] == '>') & ~grid[r][c+1] & flow_c[r][c+1])
    flow_c[r][c].prove_if(grid[r][c])
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
    if puz[r][c] != '`':  # source
        require(upstream[r][c] == int(puz[r][c]))

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

# require no two groups to come in contact.
# each group is identified by source cell number (row*width + col)
group = [[IntVar(0,width*height) for c in range(width)] for r in range(height)]
for r,c in nrange(height, width):
    if puz[r][c] != '`':  # source
        require(group[r][c] == r*width + c)
# require vertically adjacent to have the same group
for r,c in nrange(height-1, width):
    require(cond(~grid[r][c] & ~grid[r+1][c], group[r][c] == group[r+1][c], True))
# require horizontally adjacent to have the same group
for r,c in nrange(height, width-1):
    require(cond(~grid[r][c] & ~grid[r][c+1], group[r][c] == group[r][c+1], True))

# require no group of four filled cells
for r,c in nrange(height-1, width-1):
    require(~grid[r][c] | ~grid[r][c+1] | ~grid[r+1][c] | ~grid[r+1][c+1])

soln_count = 0
while solve():
    soln_count += 1
    print 'Solution %d:' % soln_count
    p(tmap(lambda g,p: '#' if g.value() else p, grid, puz))
    print
    if soln_count >= 10:
        print 'Too many solutions...'
        break
    print 'Checking for other solutions'
    x = BoolVar(True)
    for r,c in nrange(height, width):
        x = x & (grid[r][c] == grid[r][c].value())
    require(~x)

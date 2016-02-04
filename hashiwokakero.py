#!/usr/bin/python -u
#
# http://tools.qhex.org/

from claspy import *
from gridinput import *

set_max_val(width*height-1)

def cell(r,c):
    if puz[r][c] == '`':
        options = ['`']
        if r != 0 and r != height-1:
            options.append('|')
            options.append('||')
        if c != 0 and c != width-1:
            options.append('-')
            options.append('=')
        return MultiVar(*options)
    else:
        return MultiVar(int(puz[r][c]))

grid = [[cell(r,c) for c in range(width)] for r in range(height)]

def is_int(xvar):
    return xvar.boolean_op(lambda a,b: type(a) is int, None)

# require vertical lines to connect
for r,c in nrange(height-1, width):
    require(cond(grid[r][c] == '|', (grid[r+1][c] == '|') | is_int(grid[r+1][c]), True))
    require(cond(grid[r+1][c] == '|', (grid[r][c] == '|') | is_int(grid[r][c]), True))
    require(cond(grid[r][c] == '||', (grid[r+1][c] == '||') | is_int(grid[r+1][c]), True))
    require(cond(grid[r+1][c] == '||', (grid[r][c] == '||') | is_int(grid[r][c]), True))

# require horizontal lines to connect
for r,c in nrange(height, width-1):
    require(cond(grid[r][c] == '-', (grid[r][c+1] == '-') | is_int(grid[r][c+1]), True))
    require(cond(grid[r][c+1] == '-', (grid[r][c] == '-') | is_int(grid[r][c]), True))
    require(cond(grid[r][c] == '=', (grid[r][c+1] == '=') | is_int(grid[r][c+1]), True))
    require(cond(grid[r][c+1] == '=', (grid[r][c] == '=') | is_int(grid[r][c]), True))

# require sum of connections to match
for r,c in nrange(height, width):
    if puz[r][c] == '`':
        continue
    total = IntVar(0)
    if c > 0: total += cond(grid[r][c-1] == '-', 1, 0)
    if c < width-1: total += cond(grid[r][c+1] == '-', 1, 0)
    if c > 0: total += cond(grid[r][c-1] == '=', 2, 0)
    if c < width-1: total += cond(grid[r][c+1] == '=', 2, 0)
    if r > 0: total += cond(grid[r-1][c] == '|', 1, 0)
    if r < height-1: total += cond(grid[r+1][c] == '|', 1, 0)
    if r > 0: total += cond(grid[r-1][c] == '||', 2, 0)
    if r < height-1: total += cond(grid[r+1][c] == '||', 2, 0)
    require(total == grid[r][c])

def valid_vgrad(xvar):
    return xvar.boolean_op(lambda a,b: a == '|' or a == '||' or type(a) is int, None)
def valid_hgrad(xvar):
    return xvar.boolean_op(lambda a,b: a == '-' or a == '=' or type(a) is int, None)

# require connectivity
source = MultiVar(*nrange(height,width))
c_grid = [[Atom() for c in range(width)] for r in range(height)]
for r,c in nrange(height, width):
    c_grid[r][c].prove_if(source == (r,c))
    if c > 0:
        c_grid[r][c].prove_if(valid_hgrad(grid[r][c]) & valid_hgrad(grid[r][c-1]) & c_grid[r][c-1])
    if c < width-1:
        c_grid[r][c].prove_if(valid_hgrad(grid[r][c]) & valid_hgrad(grid[r][c+1]) & c_grid[r][c+1])
    if r > 0:
        c_grid[r][c].prove_if(valid_vgrad(grid[r][c]) & valid_vgrad(grid[r-1][c]) & c_grid[r-1][c])
    if r < height-1:
        c_grid[r][c].prove_if(valid_vgrad(grid[r][c]) & valid_vgrad(grid[r+1][c]) & c_grid[r+1][c])
    require(cond(grid[r][c] != '`', c_grid[r][c], True))

soln_count = 0
while solve():
    soln_count += 1
    print 'Solution %d:' % soln_count
    pgrid = tmap(str, grid)
    pgrid = tmap(lambda x: '===' if x == '=' else x, pgrid)
    pgrid = tmap(lambda x: '---' if x == '-' else x, pgrid)
    pgrid = tmap(lambda x: '|| ' if x == '||' else x, pgrid)
    pgrid = tmap(lambda x: ' | ' if x == '|' else x, pgrid)
    widths = [max([len(str(pgrid[r][c])) for r in range(height)])
              for c in range(width)]
    for row in pgrid:
        print ''.join(map(lambda val, width: str(val).center(width),
                          row, widths))
    print
    if soln_count >= 10:
        print 'Too many solutions...'
        break
    print 'Checking for other solutions'
    x = BoolVar(True)
    for r,c in nrange(height, width):
        x = x & (grid[r][c] == grid[r][c].value())
    require(~x)

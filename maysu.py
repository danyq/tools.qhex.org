#!/usr/bin/python -u
#
# http://tools.qhex.org/

from claspy import *
from gridinput import *

for r,c in nrange(height, width):
    if puz[r][c] not in ('x', 'o', '`'):
        sys.exit('unrecognized character: %s' % puz[r][c])

grid = [[MultiVar('`','<','>','^','v') for c in range(width)]
        for r in range(height)]

# require one incoming connection to every point on the path
for r,c in nrange(height, width):
    incoming = []
    if r > 0: incoming.append(grid[r-1][c] == 'v')
    if r < height-1: incoming.append(grid[r+1][c] == '^')
    if c > 0: incoming.append(grid[r][c-1] == '>')
    if c < width-1: incoming.append(grid[r][c+1] == '<')
    require(cond(grid[r][c] == '`',
                 at_most(0, incoming),
                 sum_bools(1, incoming)))

# require no elemnts pointing at each other
for r,c in nrange(height-1, width):
    require(~((grid[r][c] == 'v') & (grid[r+1][c] == '^')))
for r,c in nrange(height, width-1):
    require(~((grid[r][c] == '>') & (grid[r][c+1] == '<')))

# require straight path for 'o' and turn for 'x'
for r,c in nrange(height, width):
    if puz[r][c] != '`':
        require(grid[r][c] != '`')
    if puz[r][c] == 'o':
        if r > 0: require(cond(grid[r][c] == 'v', grid[r-1][c] == 'v', True))
        else: require(grid[r][c] != 'v')
        if r < height-1: require(cond(grid[r][c] == '^', grid[r+1][c] == '^', True))
        else: require(grid[r][c] != '^')
        if c > 0: require(cond(grid[r][c] == '>', grid[r][c-1] == '>', True))
        else: require(grid[r][c] != '>')
        if c < height-1: require(cond(grid[r][c] == '<', grid[r][c+1] == '<', True))
        else: require(grid[r][c] != '<')
    if puz[r][c] == 'x':
        if r > 0: require(cond(grid[r][c] == 'v', grid[r-1][c] != 'v', True))
        if r < height-1: require(cond(grid[r][c] == '^', grid[r+1][c] != '^', True))
        if c > 0: require(cond(grid[r][c] == '>', grid[r][c-1] != '>', True))
        if c < height-1: require(cond(grid[r][c] == '<', grid[r][c+1] != '<', True))
# loop must turn next to 'o'
for r,c in nrange(height-3, width):
    if puz[r+2][c] == 'o':
        require(~((grid[r][c] == 'v') &
                  (grid[r+1][c] == 'v') &
                  (grid[r+2][c] == 'v') &
                  (grid[r+3][c] == 'v')))
    if puz[r+1][c] == 'o':
        require(~((grid[r][c] == '^') &
                  (grid[r+1][c] == '^') &
                  (grid[r+2][c] == '^') &
                  (grid[r+3][c] == '^')))
for r,c in nrange(height, width-3):
    if puz[r][c+2] == 'o':
        require(~((grid[r][c] == '>') &
                  (grid[r][c+1] == '>') &
                  (grid[r][c+2] == '>') &
                  (grid[r][c+3] == '>')))
    if puz[r][c+1] == 'o':
        require(~((grid[r][c] == '<') &
                  (grid[r][c+1] == '<') &
                  (grid[r][c+2] == '<') &
                  (grid[r][c+3] == '<')))
# loop must be straight next to 'x'
for r in range(height):
    if puz[r][1] == 'x': require(grid[r][0] != '>')
    if puz[r][-2] == 'x': require(grid[r][-1] != '<')
for c in range(width):
    if puz[1][c] == 'x': require(grid[0][c] != 'v')
    if puz[-2][c] == 'x': require(grid[-1][c] != '^')
# incoming
for r,c in nrange(height-2, width):
    if puz[r+2][c] == 'x': require(cond(grid[r+1][c] == 'v', grid[r][c] == 'v', True))
    if puz[r][c] == 'x': require(cond(grid[r+1][c] == '^', grid[r+2][c] == '^', True))
for r,c in nrange(height, width-2):
    if puz[r][c+2] == 'x': require(cond(grid[r][c+1] == '>', grid[r][c] == '>', True))
    if puz[r][c] == 'x': require(cond(grid[r][c+1] == '<', grid[r][c+2] == '<', True))
# outgoing
for r,c in nrange(height-1, width):
    if puz[r][c] == 'x': require(cond(grid[r][c] == 'v', grid[r+1][c] == 'v', True))
    if puz[r+1][c] == 'x': require(cond(grid[r+1][c] == '^', grid[r][c] == '^', True))
for r,c in nrange(height, width-1):
    if puz[r][c] == 'x': require(cond(grid[r][c] == '>', grid[r][c+1] == '>', True))
    if puz[r][c+1] == 'x': require(cond(grid[r][c+1] == '<', grid[r][c] == '<', True))

# require connectivity along path
c_grid = [[Atom() for c in range(width)] for r in range(height)]
for r,c in nrange(height-1, width):
    c_grid[r][c].prove_if(c_grid[r+1][c] & (grid[r+1][c] == '^'))
    c_grid[r+1][c].prove_if(c_grid[r][c] & (grid[r][c] == 'v'))
for r,c in nrange(height, width-1):
    c_grid[r][c].prove_if(c_grid[r][c+1] & (grid[r][c+1] == '<'))
    c_grid[r][c+1].prove_if(c_grid[r][c] & (grid[r][c] == '>'))
# the first x/o is proven
for r,c in nrange(height, width):
    if puz[r][c] != '`':
        c_grid[r][c].prove_if(True)
        break
for r,c in nrange(height, width):
    require(cond(grid[r][c] != '`', c_grid[r][c], True))

# break symmetry for direction
for r,c in nrange(height, width):
    if puz[r][c] == 'o':
        require((grid[r][c] == '>') | (grid[r][c] == 'v'))
        break

soln_count = 0
while solve():
    soln_count += 1
    print 'Solution %d:' % soln_count
    output = [['   ' if c%2 else ' ' for c in range(width*2)] for r in range(height*2)]
    for r,c in nrange(height, width):
      output[r*2][c*2] = puz[r][c]
      if grid[r][c].value() == '>': output[r*2][c*2+1] = '---'
      if grid[r][c].value() == '<': output[r*2][c*2-1] = '---'
      if grid[r][c].value() == '^': output[r*2-1][c*2] = '|'
      if grid[r][c].value() == 'v': output[r*2+1][c*2] = '|'
    print '\n'.join([''.join(row) for row in output])
    if soln_count >= 10:
        print 'Too many solutions...'
        break
    print 'Checking for other solutions'
    x = BoolVar(True)
    for r,c in nrange(height, width):
        x = x & (grid[r][c] == grid[r][c].value())
    require(~x)

#!/usr/bin/python -u
#
# http://tools.qhex.org/

from claspy import *
import sys

def nrange(*dim_sizes):
    """Returns an iterator of all coordinates within the given dimensions."""
    if len(dim_sizes) == 1:
        for i in range(dim_sizes[0]):
            yield (i,)
        return
    for i in range(dim_sizes[0]):
        for rest in apply(nrange, dim_sizes[1:]):
            yield (i,) + rest

puz = sys.stdin.read().strip()
lines = map(lambda line: line.rstrip(), puz.split('\n'))
mode = lines[0]
if mode not in ('translation', 'rotation', 'reflection'):
    print 'Error: mode not recognized.'
    print 'The first line must be one of:'
    print
    print 'translation'
    print 'rotation'
    print 'reflection'
    sys.exit()
pieces = '\n'.join(lines[1:])
pieces = filter(bool, pieces.split('\n\n'))
pieces = map(lambda piece: map(list, piece.split('\n')), pieces)
board = pieces[0]
pieces = pieces[1:]

board_area = sum(map(lambda x: x!=" ", reduce(lambda a,b: a+b, board)))
piece_area = sum(map(lambda x: x!=" ", reduce(lambda a,b: a+b,
                                              reduce(lambda a,b: a+b, pieces))))
if piece_area > board_area:
    print 'solving with overlaps'
    print 'piece area', piece_area, 'board area', board_area
    print
if piece_area < board_area:
    print 'solving with empty space'
    print 'piece area', piece_area, 'board area', board_area
    print

height = len(board)
width = max(map(len, board))

piece_vars = []

# For each piece, render the piece in every possible position, onto
# two grids. grid_b is a grid of 0 or 1 indicating the presence of the
# piece. This is used for computing constraints efficiently. grid_c is
# a grid of whitespace with the characters of the piece rendered in
# it, used for the final output.
for piece in pieces:
    positions = []  # list of (grid_b, grid_c)
    for d_r, d_c, trans, flip1, flip2 in nrange(height, width, 2, 2, 2):
        if mode == 'translation' and (trans or flip1 or flip2): continue
        if mode == 'rotation' and trans + flip1 + flip2 not in (0, 2): continue
        grid_b = [[0 for c in range(width)] for r in range(height)]
        grid_c = [[None for c in range(width)] for r in range(height)]
        invalid = False
        for p_r in range(len(piece)):
            for p_c in range(len(piece[p_r])):
                if piece[p_r][p_c] != ' ':
                    r,c = p_r,p_c
                    # apply transformations
                    if trans: r,c = c,r
                    if flip1: r = -r
                    if flip2: c = -c
                    r += d_r
                    c += d_c
                    if r < 0 or r >= height or c < 0 or c >= width or \
                            len(board[r]) <= c or board[r][c] == ' ':
                        invalid = True
                        break
                    grid_b[r][c] = 1
                    grid_c[r][c] = piece[p_r][p_c]
            if invalid: break
        if not invalid:
            positions.append((grid_b, grid_c))
    if positions == []:
        print '\nno possible positions for piece:\n'
        print join(piece, '\n', '')
        print '\nwithin shape:\n'
        print join(board, '\n', '')
        sys.exit()
    # convert all lists to tuples
    positions = map(lambda a: tuple(map(lambda b: tuple(map(tuple, b)), a)),
                    positions)
    positions = set(map(tuple, positions))
    piece_vars.append(MultiVar(*positions))
    print len(positions), 'placements for piece'

# require each grid square to have one piece
print
for r in range(len(board)):
    for c in range(len(board[r])):
        if board[r][c] != ' ':
            if piece_area < board_area:
                require(at_most(1, [grid_b[r][c] for grid_b, grid_c in piece_vars]))
            elif piece_area > board_area:
                require(at_least(1, [grid_b[r][c] for grid_b, grid_c in piece_vars]))
            else:
                require(sum_bools(1, [grid_b[r][c] for grid_b, grid_c in piece_vars]))

soln_count = 0
while solve():
    soln_count += 1
    print 'Solution %d:' % soln_count
    soln = [['' if c < len(board[r]) else ' '
             for c in range(width)] for r in range(height)]
    for r, c, i in nrange(height, width, len(piece_vars)):
        piece_grid_b, piece_grid_c = piece_vars[i].value()
        if piece_grid_b[r][c]:
            soln[r][c] += piece_grid_c[r][c]
    max_w = 0
    for r, c in nrange(height, width):
        if soln[r][c] == '': soln[r][c] = board[r][c]
        max_w = max(max_w, len(soln[r][c]))
    print '\n'.join(map(lambda row: ' '.join(map(lambda x: x.center(max_w), row)), soln))
    print
    if soln_count >= 10:
        print 'Too many solutions...'
        break
    print 'Checking for other solutions'
    x = BoolVar(True)
    for piece_var in piece_vars:
        x = x & (piece_var == piece_var.value())
    require(~x)

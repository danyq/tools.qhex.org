#!/usr/bin/python -u
#
# http://tools.qhex.org/

import sys
import os
import subprocess
import signal
import time

input_str = sys.stdin.read()

puzzles = '''\
maysu
sudoku
lightsout
thermometers
kakuro
fillapix
minesweeper
hitori
nurikabe
tapa
hashiwokakero
numberlink
shikaku
fillomino'''
puzzles = puzzles.split('\n')

start_time = time.time()
here = os.path.dirname(__file__)
for puzzle in puzzles:
    p = subprocess.Popen( \
        [os.path.join(here, '%s.py' % puzzle)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=1)
    p.stdin.write(input_str)
    p.stdin.close()
    stdout = ''
    for line in iter(p.stdout.readline, ''):
        if line.startswith('Solution 2'):
            try:
                if p.poll() is None:
                    os.kill(p.pid, signal.SIGKILL)
                    # This may not kill the clasp subprocess. :(
                    # Normally we could use setsid and kill the group,
                    # but wsgi needs to be able to kill gridpuzzle and all children.
            except OSError, err:
                print err
            stdout = 'killed'
            break
        stdout += line
    t = '[%.1fs]' % (time.time() - start_time)
    if stdout == 'killed':
        print t, puzzle + ': multiple solutions'
        continue
    stderr = p.stderr.read()
    if len(stderr) > 0:
        print t, puzzle + ': invalid'
        continue
    if '\nSATISFIABLE' not in stdout:
        if '\nUNSATISFIABLE' in stdout:
            print t, puzzle + ': no solutions'
        else:
            print t, puzzle + ': invalid'
        continue
    print
    printing = False
    for line in stdout.split('\n'):
        if line.startswith('Checking for other solutions'):
            printing = False
        if line.startswith('Solution '):
            printing = True
            print t, puzzle, 'solution:'
        elif printing:
            print line

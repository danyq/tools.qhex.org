#!/usr/bin/python -u
#
# http://tools.qhex.org/

from pprint import pprint as pp
import sys
import os
import subprocess
import shlex
import re
import sre_constants
import math

input_str = sys.stdin.read()
lines = input_str.split('\n')
blocks = '\n'.join(lines).strip('\n').split('\n\n')
if len(blocks) <= 1:
    print input_str
    print
    print 'no commands entered'
    sys.exit()
commands = blocks[-1].strip().split('\n')
input_str = '\n\n'.join(blocks[:-1]).rstrip()

class CommandError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

def cmd_split(input_str, sep):
    if type(input_str) is list:
        return map(lambda x: cmd_split(x, sep), input_str)
    if sep == '':
        return list(input_str)
    return input_str.split(sep)

def cmd_join(input_str, sep):
    if type(input_str) is not list:
        raise CommandError('not enough dimensions to join in input')
    if type(input_str[0]) is list:
        return map(lambda x: cmd_join(x, sep), input_str)
    return sep.join(input_str)

def to_coord(input_str, coords=None, prefix=()):
    '''Takes a structure of nested lists and returns a dictionary from
    coordinate to value.'''
    if coords is None:
        coords = {}
        to_coord(input_str, coords)
        return coords
    if type(input_str) is not list:
        coords[prefix] = input_str
    else:
        map(lambda i: to_coord(input_str[i], coords, prefix + (i,)),
            range(len(input_str)))

def from_coord(coords, prefix=()):
    '''Takes a coordinate dictionary and returns nested lists.'''
    if len(prefix) == len(iter(coords).next()):
        return coords[prefix] if prefix in coords else ''
    else:
        axis = len(prefix)
        max_index = max([c[axis] for c in coords])
        return [from_coord(coords, prefix + (i,))
                for i in range(max_index + 1)]

def cmd_transpose(input_str, *args):
    coords = to_coord(input_str)
    num_axes = len(iter(coords).next())
    if not args:
        return cmd_transpose(input_str, '1', '0', *range(2, num_axes))
    if len(args) != num_axes:
        raise CommandError('Dimensions for transpose do not match. Table has dimension %d.' %
                           num_axes)
    new_axes = map(int, args)
    for i in range(len(new_axes)):
        if i not in new_axes:
            raise CommandError('Transpose arguments are not a valid permutation.')
    new_coords = {}
    for c in coords:
        new_c = tuple([c[i] for i in new_axes])
        new_coords[new_c] = coords[c]
    return from_coord(new_coords)

def cmd_replace(input_str, pattern, replacement):
    if type(input_str) is list:
        return [cmd_replace(x, pattern, replacement) for x in input_str]
    return re.sub(pattern, replacement, input_str)

def cmd_strip(input_str):
    if type(input_str) is not list:
        return input_str.strip()
    return filter(lambda x: bool(x), map(cmd_strip, input_str))

def cmd_chunk(input_str, *args):
    if not args: return input_str
    # chunk size of zero means skip this dimension
    if type(input_str) is list and args[0] == 0:
        return map(lambda x: cmd_chunk(x, *args[1:]), input_str)
    coords = to_coord(input_str)
    num_axes = len(iter(coords).next())
    if len(args) > num_axes:
        raise CommandError('Not enough dimensions to chunk in input.')
    new_coords = {}
    for c in coords:
        new_chunk_coord = []
        new_sub_coord = []
        for i in range(num_axes):
            if i < len(args):
                new_chunk_coord.append(c[i] // args[i])
                new_sub_coord.append(c[i] % args[i])
            else:
                new_sub_coord.append(c[i])
        new_coords[tuple(new_chunk_coord + new_sub_coord)] = coords[c]
    return from_coord(new_coords)

def cmd_factor(input_str):
    x = len(input_str)
    factors = [(i, x//i) for i in range(2, x//2 + 1) if i * (x//i) == x]
    raise CommandError('Please specify a chunk size.\n' +
                       'Input length: %d\n' % x + 'Possible factors: ' +
                       ' '.join(['%dx%d' % f for f in factors]))

def one_slice(input_str, spec):
    '''Takes an input and a spec string such as "1:10:2" and returns
    input[1:10:2]. Always returns a slice, so if the spec is "5",
    returns input[5:6].'''
    spec = spec.split(':')
    spec = map(lambda x: int(x) if x != '' else None, spec)
    if len(spec) == 1:
        return input_str[spec[0]:spec[0]+1]
    return input_str.__getitem__(slice(*spec))

def cmd_slice(input_str, *slices):
    '''Performs a multi-dimensional slice. Each slice argument is a slice
    along one dimension, and may also have multiple comma-separated
    sections, such as "1:3,5:7".'''
    spec = slices[0]
    result = [one_slice(input_str, part) for part in spec.split(',')]
    result = reduce(lambda a,b: a+b, result)
    is_index = ',' not in spec and ':' not in spec
    if is_index: result = result[0]
    if len(slices) == 1: return result
    if is_index:
        return cmd_slice(result, *slices[1:])
    else:
        return [cmd_slice(elt, *slices[1:]) for elt in result]

def cmd_print(x, seq=None, align='right'):
    """Prints a multidimensional list given a seqence of horizontal or
    vertical concatenations for each dimension, starting with the
    outermost.  The numerical digit indicates how much padding to
    insert at each level."""
    def depth(x):
        if type(x) is not list:
            return 0
        return max(map(depth, x)) + 1
    d = depth(x)
    if seq is None:
        if d == 0:
            return x
        elif d == 1:
            return cmd_print(x, 'v0', 'left')
        else:
            seq = 'h1'
            for i in range(d - 1):
                seq = 'v' + str(i) + seq
            return cmd_print(x, seq, align)
    if len(seq) % 2 == 1:
        raise CommandError('invalid print sequence')
    if d * 2 > len(seq):
        return map(lambda xi: cmd_print(xi, seq, align), x)
    if d * 2 < len(seq):
        raise CommandError('print sequence too long for table of dimension %d' % d)
    if type(seq) is not str:
        raise TypeError("Sequence is not a string! " + str(seq))
    if align not in ('left', 'center', 'right'):
        raise CommandError('invalid text alignment: ' + align)
    def recurse(x, seq):
        """Returns a 2D array based on the sequence of concatentations."""
        if seq == '':
            return [[str(x).encode('string_escape')]]  # base case is a 2D array
        if type(x) is not list:
            raise ValueError('Subtree not deep enough for print sequence ' + seq)
        direction = seq[0]
        separator_count = seq[1]
        if direction not in 'hv' or separator_count not in '0123456789':
            raise CommandError('invalid print sequence')
        separator_count = int(separator_count)
        subarrays = map(lambda elt: recurse(elt, seq[2:]), x)
        if direction == 'v':  # vertical concatenation
            sep = [[] for n in range(separator_count)]
            result = reduce(lambda a, b: a + sep + b, subarrays)
            # make it rectangular
            max_cols = max(map(len, result))
            return [row + [' ']*(max_cols - len(row)) for row in result]
        else:  # horizontal concatenation
            max_rows = max(map(len, subarrays))
            sep = [' ' for n in range(separator_count)]
            return [reduce(lambda a, b: a + sep + b,
                           map(lambda subarray:
                                   subarray[r] if r < len(subarray) \
                                   else [' ']*len(subarray[0]),
                               subarrays))
                    for r in range(max_rows)]
    a = recurse(x, seq)
    num_cols = len(a[0])
    for row in a:
        if len(row) != num_cols:
            raise ValueError('Array not rectangular')
    column_widths = [max(map(lambda row: len(row[c]), a))
                     for c in range(num_cols)]
    result = []
    for row in a:
        s = ""
        for c in range(len(row)):
            if align == 'left':
                s += row[c].ljust(column_widths[c])
            elif align == 'center':
                s += row[c].center(column_widths[c])
            elif align == 'right':
                s += row[c].rjust(column_widths[c])
        result.append(s)
    return '\n'.join(result)

tools = os.listdir(os.path.dirname(__file__))
tools = set(map(lambda s: s.split('.')[0], tools))
tools.remove('format')
tool_run = False  # has a tool been run? (only one is allowed)

for command in commands:
    if command.startswith('#'):
        continue
    cmd_parts = shlex.split(command)
    cmd, args = cmd_parts[0], cmd_parts[1:]
    command_joined = command.replace(' ','').lower()
    args_unescape = map(lambda s: s.decode('string_escape'), args)
    print_result = True
    try:
        if cmd == 'split':
            if not args: raise CommandError('split takes at least 1 argument')
            for arg in args_unescape:
                input_str = cmd_split(input_str, arg)
        elif cmd == 'join':
            if not args: raise CommandError('join takes at least 1 argument')
            for arg in args_unescape[::-1]:
                input_str = cmd_join(input_str, arg)
        elif cmd == 'transpose':
            input_str = cmd_transpose(input_str, *args)
        elif cmd == 'replace':
            if len(args) < 2 or len(args) % 2 != 0:
                raise CommandError('replace requires an even number of arguments')
            for i in range(0,len(args),2):
                input_str = cmd_replace(input_str, args[i], args[i+1])
        elif cmd == 'strip':
            if args: raise CommandError('strip takes no arguments')
            input_str = cmd_strip(input_str)
        elif cmd == 'chunk':
            if len(args) == 0: input_str = cmd_factor(input_str)
            else: input_str = cmd_chunk(input_str, *map(int, args))
        elif cmd == 'slice':
            if not args: raise CommandError('slice takes at least 1 argument')
            input_str = cmd_slice(input_str, *args)
        elif cmd == 'print':
            if len(args) > 2: raise CommandError('print takes no more than 2 arguments')
            input_str = cmd_print(input_str, *args)
        elif command_joined in tools:
            if tool_run: raise CommandError('only one tool can be used at a time')
            tool_run = True
            print_result = False
            print input_str
            print
            print 'running', command_joined
            print
            p = subprocess.Popen([os.path.join(os.path.dirname(__file__),
                                               '%s.py' % command_joined)],
                                 stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 bufsize=1)
            if type(input_str) is not str:
                print 'WARNING: Input is not a string.'
                print 'You may want to use "print" or "join" first.'
                print
                input_str = str(input_str)
            p.stdin.write(input_str)
            p.stdin.close()
            result = []
            for line in iter(p.stdout.readline, ''):
                print line,
                result.append(line)
            err = p.stderr.read()
            if err:
                print
                raise CommandError(err)
            input_str = ''.join(result)
            print
            print 'completed', command_joined
            print
        else:
            raise CommandError('unknown command')
    except CommandError as e:
        print 'Error executing command:', command
        print
        print e.value
        print
        pp(input_str)
        sys.exit()
    except sre_constants.error as e:
        print 'Regex error:', e
        print
        print 'If you\'re using one of .^$*+?{}()[]|\\'
        print 'and don\'t want a regular expression'
        print 'you may need to put a \ before it.'
        sys.exit()

if print_result:
    if type(input_str) is list:
        pp(input_str)
    else:
        print input_str

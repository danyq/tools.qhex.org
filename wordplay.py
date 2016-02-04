#!/usr/bin/python -u
#
# http://tools.qhex.org/

import sys
import os
import re
from math import factorial
import itertools
from time import time

# dictionary sorted by frequency
# location relative to program
SORTED_DICT = '../dict/sortedwords.txt'

input = sys.stdin.read().strip()

# each filter function yields a set of regex patterns

def anagram(letters):
    '''rearrange the given letters'''
    yield '.' * len(letters)  # length constraint
    for c in set(letters):
        yield '(.*%c.*){%d}' % (c, letters.count(c))
    yield '(?!%s).*' % letters  # not identical

def subanagram(letters):
    '''rearrange at most the given letters'''
    yield '.{1,%d}' % len(letters)  # length constraint
    for c in set(letters):
        others = ''.join(set(letters) - set(c))
        yield '([%s]*%c?[%s]*){1,%d}' % (others, c, others, letters.count(c))
    yield '(?!%s).*' % letters  # not identical

def superanagram(letters):
    '''rearrange at least the given letters'''
    yield '.{%d,}' % len(letters)  # length constraint
    for c in set(letters):
        yield '(.*%c.*){%d}' % (c, letters.count(c))
    yield '(?!%s).*' % letters  # not identical

def transdelete(letters, n=1):
    '''rearrange all but n of the given letters'''
    if n >= len(letters):
        print 'can\'t transdelete', n, 'letters from', s
        sys.exit()
    yield '.' * (len(letters) - n)  # length constraint
    for c in set(letters):
        others = ''.join(set(letters) - set(c))
        yield '([%s]*%c?[%s]*){1,%d}' % (others, c, others, letters.count(c))

def transadd(letters, n=1):
    '''rearrange all of the given letters plus n wildcards'''
    yield '.' * (len(letters) + n)  # length constraint
    for c in set(letters):
        yield '(.*%c.*){%d}' % (c, letters.count(c))

def bank(letters):
    '''use the same set of unique letters'''
    yield '[%s]+' % ''.join(set(letters))
    for c in set(letters):
        yield '.*%c.*' % c
    yield '(?!%s).*' % letters  # not identical

def subbank(letters):
    '''use at most the same set of unique letters'''
    yield '[%s]+' % ''.join(set(letters))
    yield '(?!%s).*' % letters  # not identical

def superbank(letters):
    '''use at least the same set of unique letters'''
    for c in set(letters):
        yield '.*%c.*' % c
    yield '(?!%s).*' % letters  # not identical

def delete(s, n=None):
    '''achievable by deleting n letters from the given string (or any
    number, if n is omitted.'''
    if n is not None:
        if n >= len(s):
            print 'can\'t delete', n, 'letters from', s
            sys.exit()
        yield '.' * (len(s) - n)
    yield '?'.join(s) + '?'

def add(s, n=None):
    '''achievable by inserting n letters into the given string (or any
    number, if n is omitted.'''
    if n is not None:
        yield '.' * (len(s) + n)
    yield '.*' + '.*'.join(s) + '.*'

def change(s, n=1):
    '''change n letters'''
    if n > len(s):
        print 'can\'t change', n, 'letters in', s
        sys.exit()
    complexity = reduce(lambda x,y:x*y,
                        (float(len(s)-i)/(i+1) for i in range(n)),
                        1)
    if complexity > 25000:
        print 'sorry, this command is too complex for the current algorithm:'
        print 'change %d: %s' % (n, s)
        sys.exit()
    yield '.' * len(s)
    def expressions(s, n):
        if len(s) < n: raise StopIteration
        if n == 0:
            yield s
        else:
            for rest in expressions(s[1:], n-1):
                yield '[^%c]' % s[0] + rest
            for rest in expressions(s[1:], n):
                yield s[0] + rest
    yield '|'.join(list(expressions(s, n)))

def substring(s):
    '''included in the given string'''
    result = []
    for i in range(len(s)):
        for j in range(i+1,len(s)+1):
            result.append(s[i:j])
    yield '|'.join(result)

periodic = 'H|He|Li|Be|B|C|N|O|F|Ne|Na|Mg|Al|Si|P|S|Cl|Ar\
|K|Ca|Sc|Ti|V|Cr|Mn|Fe|Co|Ni|Cu|Zn|Ga|Ge|As|Se|Br|Kr\
|Rb|Sr|Y|Zr|Nb|Mo|Tc|Ru|Rh|Pd|Ag|Cd|In|Sn|Sb|Te|I|Xe\
|Cs|Ba|Hf|Ta|W|Re|Os|Ir|Pt|Au|Hg|Tl|Pb|Bi|Po|At|Rn\
|Fr|Ra|Rf|Db|Sg|Bh|Hs|Mt|Ds|Rg|Cn|Uut|Fl|Uup|Lv|Uus|Uuo\
|La|Ce|Pr|Nd|Pm|Sm|Eu|Gd|Tb|Dy|Ho|Er|Tm|Yb|Lu\
|Ac|Th|Pa|U|Np|Pu|Am|Cm|Bk|Cf|Es|Fm|Md|No|Lr'

states = '''\
AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|\
HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|\
MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|\
NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|\
SD|TN|TX|UT|VT|VA|WA|WV|WI|WY'''

def increment_references(s):
    '''Increment all group references in the expression by one.
    This hides the implicit group that is added around all expressions.'''
    i = 0
    result = ''
    while i < len(s):
        result += s[i]
        if s[i] != '\\' or i == len(s) - 1:  # not a \ escape
            i += 1
        elif s[i+1] not in '123456789':  # not a \number escape
            result += s[i+1]
            i += 2
        elif i + 2 == len(s) or s[i+2] not in '0123456789':  # not a \xx escape
            result += str(int(s[i+1]) + 1)
            i += 2
        elif i + 3 == len(s) or s[i+3] not in '0123456789':  # not a \xxx escape
            result += str(int(s[i+1:i+3]) + 1)
            i += 3
        else:  # probably an octal \xxx escape
            result += s[i+1:i+4]
            i += 4
    return result

def process_cmd(line):
    '''takes a command and returns a list of regex expressions'''
    line = line.strip().lower()
    if not line: return []
    if '%' in line:
        print 'substitution (%) can only be used after "=>"'
        sys.exit()
    if ':' in line:
        cmd, arg = line.split(':', 1)
        param = ''
        if ' ' in cmd:
            cmd, param = cmd.split(' ', 1)
            param = param.strip()
        cmd = cmd.strip()
        arg = arg.strip()
        if cmd == 'anagram': f = anagram
        elif cmd == 'subanagram': f = subanagram
        elif cmd == 'superanagram': f = superanagram
        elif cmd == 'transdelete': f = transdelete
        elif cmd == 'transadd': f = transadd
        elif cmd == 'bank': f = bank
        elif cmd == 'subbank': f = subbank
        elif cmd == 'superbank': f = superbank
        elif cmd == 'delete': f = delete
        elif cmd == 'add': f = add
        elif cmd == 'change': f = change
        elif cmd == 'substring': f = substring
        else:
            print 'unknown command:', cmd
            sys.exit()
        if arg == '':
            print 'no input provided for', cmd
            sys.exit()
        arg = ''.join(arg.split())  # remove spaces
        if any(c not in 'abcdefghijklmnopqrstuvwxyz' for c in arg):
            print 'invalid characters in:', arg
            sys.exit()
        if param == '':
            return list(f(arg))
        elif cmd in ['transdelete', 'transadd', 'delete', 'add', 'change']:
            if not param.isdigit():
                print 'parameter to', cmd, 'must be a number:', param
                sys.exit()
            return list(f(arg, int(param)))
        else:
            print cmd, 'does not accept a parameter:', param
            sys.exit()
    line = line.replace('\p', '(%s)' % periodic)
    line = line.replace('\s', '(%s)' % states)
    if line[0] == '!': line = '(?!%s).*' % line[1:]
    line = increment_references(line)
    return [line]

here = os.path.dirname(__file__)
f = open(os.path.join(here, SORTED_DICT))
file_cache = []  # list of 500kb chunks
cache_end_pos = 0  # position in file of the end of the cache
CACHE_LIMIT = 200  # max number of 500kb chunks to cache (50MB)

def single_search(commands, enable_cache, max_results=None):
    '''takes a list of commands and yields matching words. occasionally
    yields None to avoid getting stuck in sub searches.'''
    global file_cache, cache_end_pos
    queries = sum(map(process_cmd, commands), [])
    if len(queries) == 0:
        print 'please enter some conditions'
        sys.exit()
    count = 0
    chunk = 0
    fpos = 0  # current file position
    while True:
        # process 500kb at a time
        if chunk < len(file_cache):
            s = file_cache[chunk]
            #print chunk, 'in cache'
        else:
            if chunk == len(file_cache):
                fpos = cache_end_pos
                #print chunk, 'going to end of cache'
            f.seek(fpos)  # recover position
            #print chunk, 'reading'
            s = ''.join(f.readlines(500000))
            s = s.strip()
            fpos = f.tell()  # save position
            if chunk < CACHE_LIMIT and enable_cache:
                file_cache.append(s)
                cache_end_pos = fpos
                #print chunk, 'extending cache'
        chunk += 1

        if not s: break
        for query in queries:
            pattern = re.compile('^('+query+')$', re.M | re.I)
            results = pattern.findall(s)
            if not results: break
            if type(results[0]) is tuple:
                results = [r[0] for r in results]
            results = filter(lambda r: '\n' not in r, results)
            s = '\n'.join(results)
        for r in results:
            yield r
            count += 1
            if max_results is not None and count >= max_results:
                raise StopIteration
        yield None

FIRST_PASS_LIMIT = 1000  # max number of results for first pass
SECOND_PASS_EACH_LIMIT = 20  # max number of results for each second pass search
DISPLAY_LIMIT = 500  # number of results to output

sub_dict = []  # saved dictionary results for substitution
def multi_search(commands):
    '''takes a list of commands and performs a search. if there is an
    existing sub-dictionary, then substitutes each word in turn and
    performs separate searches.'''
    assert sub_dict
    if not any('%' in cmd for cmd in commands):
        print 'substitution (%) must be used somewhere after "=>"'
        sys.exit()
    # start a search on each sub word
    sub_searches = []  # list of (sub_word, search iterator)
    for sub_word in sub_dict:
        sub_commands = map(lambda cmd: cmd.replace('%', sub_word), commands)
        sub_searches.append((sub_word,
                             single_search(sub_commands, True,
                                           SECOND_PASS_EACH_LIMIT)))
    results = {}  # result word => list of matching sub words
    count = 0
    keep_going = True
    while keep_going:
        keep_going = False
        for sub_word, sub_search in sub_searches:
            try:
                result = sub_search.next()
            except StopIteration:
                continue
            if result is None: continue
            keep_going = True
            yield sub_word.ljust(10) + ' => ' + result

if '=>' in input:  # cross-filter
    first_cmds, sub_cmds = input.split('=>', 1)
    first_cmds = first_cmds.strip().split('\n')
    sub_cmds = sub_cmds.strip().split('\n')
    if '=>' in sub_cmds:
        print 'only one cross-filter operation (=>) allowed'
        sys.exit()
    for word in single_search(first_cmds, True, FIRST_PASS_LIMIT):
        if word is not None:
            sub_dict.append(word)
    results = multi_search(sub_cmds)
else:  # regular search
    results = single_search(input.split('\n'), False)

count = 0
for result in results:
    if result is None: continue
    print result
    count += 1
    if count > DISPLAY_LIMIT:
        print '...\n\n(too many results)'
        sys.exit()

if count == 0:
    print 'no results found'


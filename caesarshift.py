#!/usr/bin/python -u
#
# http://tools.qhex.org/

import sys
import dictionary

MAX_WORD_LEN = 20

input = sys.stdin.read().strip().replace('\n',' ')

def rot(s, n):
    result = ''
    for c in s:
        x = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.find(c.upper())
        if x != -1:
            new_c = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[(x + n) % 26]
            if c == c.lower():
                new_c = new_c.lower()
            result += new_c
        else:
            result += c
    return result

def highlight(s):
    '''Returns a string of '^' characters highlighting any words in s.'''
    result = [' '] * len(s)
    for i in range(len(s)):
        for j in range(i, min(len(s) + 1, i + MAX_WORD_LEN)):
            score = dictionary.score(s[i:j].lower())
            if score > 0 and j-i+score > 7:  # ignore short rare words
                for k in range(i, j):
                    result[k] = '^'
    return ''.join(result)

for n in range(26):
    s = rot(input, n)
    print ('+'+str(n)).rjust(3), ('-'+str((26-n)%26)).rjust(3), '', s
    print '        ', highlight(s)


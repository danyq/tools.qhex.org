#!/usr/bin/python -u
#
# http://tools.qhex.org/

import sys
from copy import deepcopy
import dictionary

puz = sys.stdin.read().strip()
puz, sep, given_words = puz.partition('\n\n')
puz = filter(lambda x: x not in ' \t', puz)
puz = map(list, puz.split('\n'))
puz_blanked = deepcopy(puz)
puz_filled = [['`'] * len(row) for row in puz]
given_words = set(map(lambda w: w.lower(), given_words.split()))

MIN_WORD_SCORE = 1

# find all words
words = []
for r in range(len(puz)):
  for c in range(len(puz[r])):
    for dr,dc in [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]:
        r1,c1 = r,c
        word = ''
        best_word = None
        best_word_score = MIN_WORD_SCORE - 0.0001
        while r1 >= 0 and c1 >= 0 and r1 < len(puz) and c1 < len(puz[r1]):
            word += puz[r1][c1].lower()
            score = dictionary.score(word)
            if score > 0: score = len(word)-3 + score*0.5
            if word in given_words:
              for i in range(len(word)):
                puz_blanked[r+dr*i][c+dc*i] = '`'
                puz_filled[r+dr*i][c+dc*i] = word[i].upper()
            elif score > best_word_score:
              best_word_score = score
              best_word = word
            r1 += dr
            c1 += dc
        if best_word:
            s = 'row %d col %d' % (r+1,c+1)
            if dr == -1: s += ' up'
            if dr == 1: s += ' down'
            if dc == -1: s += ' left'
            if dc == 1: s += ' right'
            words.append([best_word_score,best_word,s])

if given_words:
  print '\n'.join(map(lambda row: ' '.join(row), puz_filled))
  print
print '\n'.join(map(lambda row: ' '.join(row), puz_blanked))
print

if not words:
  print 'error: no words found'
  sys.exit()

words.sort(reverse=True)
max_len = max(map(lambda x: len(x[1]), words))
for score, word, s in words[:150]:
  print word.ljust(max_len), s
if len(words) > 150:
  print '...'

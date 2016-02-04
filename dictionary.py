
# http://tools.qhex.org/
#
# A function for dictionary searches. Returns an integer score, zero
# if the input was not found.
#
# This uses a sorted dictionary file containing integer scores for
# each word. It stores the dictionary in memory as a string and uses
# binary search to find words. This is much slower to query than
# loading it into a python dictionary, but uses less memory.

import os
here = os.path.dirname(__file__)
dict_file = open(os.path.join(here, '../dict/scoredwords.txt'))
dict_str = dict_file.read()
dict_file.close()

def score_rec(word, startpos=0, endpos=len(dict_str)+1):
    if startpos >= endpos: return 0
    mid = (endpos+startpos)//2
    mid_start = dict_str.rfind('\n', 0, mid) + 1
    mid_end = dict_str.find('\n', mid, len(dict_str))
    if mid_end == -1: mid_end = len(dict_str)
    mid_word, mid_score = dict_str[mid_start:mid_end].split(' ')
    if mid_word > word:
        return score_rec(word, startpos, mid_start)
    if mid_word < word:
        return score_rec(word, mid_end+1, endpos)
    return int(mid_score)

def score(word):
    if len(word) > 34:
        return 0
    if any([c not in 'abcdefghijklmnopqrstuvwxyz' for c in word]):
        return 0
    return score_rec(word)

#!/usr/bin/python -u
#
# http://tools.qhex.org/

import sys

def all_counts(lst):
    '''Prints a histogram of the input elements, sorted by element.'''
    counts = dict.fromkeys(lst, 0)
    for i in lst:
        counts[i] += 1
    #if ' ' in counts: del counts[' ']
    if not counts: return
    maxcount = max(counts.values())
    for elt in sorted(counts.keys()):
        hist = ""
        for i in range(counts[elt]/(maxcount//50+1)):
            hist += "#"
        print repr(elt), str(counts[elt]).rjust(len(str(maxcount))), hist

def top_counts(lst, padding = 0, n = 50):
    '''Prints a histogram of the top N elements, sorted by frequency.'''
    counts = dict.fromkeys(lst, 0)
    for i in lst:
        #if ' ' in i or '\n' in i:
        #    if i in counts: del counts[i]
        #    continue
        counts[i] += 1
    sort_list = [(count, elt) for elt, count in counts.iteritems()]
    sort_list.sort(reverse=True)
    if not sort_list: return
    maxcount = max([count for count, elt in sort_list])
    for count, elt in sort_list[:n]:
        hist = ""
        for i in range(count/(maxcount//50+1)):
            hist += "#"
        print repr(elt).ljust(padding), str(count).rjust(len(str(maxcount))), hist
    if len(sort_list) > n:
        print '...'

# Suffix trees
#
# Each node is a list of a value and any branches.
# The value represents a prefix repeated in all branches.
# The root node has a value of ''.
#
# For example, the strings 'abcdef' and 'abcghi' would be represented as:
# ['', ['abc', ['def'], ['ghi']]]
#
# The strings 'abc' and 'abcdef' would be represented as:
# ['', ['abc', [''], ['def']]] 

def common_prefix_len(a, b):
    '''Returns the length of any common prefix between strings A and B.'''
    for i in range(min(len(a), len(b))):
        if a[i] != b[i]:
            return i
    return i + 1

def add_to_tree(tree, s):
    '''Add a string to a tree.'''
    branches = tree[1:]
    found = False
    for branch in branches:
        prefix_len = common_prefix_len(branch[0], s)
        if prefix_len > 0:
            if prefix_len < len(branch[0]):
                branch[:] = [s[:prefix_len],
                              [branch[0][prefix_len:]] + branch[1:],
                              [s[prefix_len:]]]
            elif prefix_len < len(s):
                add_to_tree(branch, s[prefix_len:])
            else:  # branch exactly matches s
                branch.append([''])
            found = True
            break
    if not found:
        tree.append([s])

def suffix_tree(s):
    '''Return the suffix tree for a string.'''
    tree = ['']
    for i in range(len(s)):
        #if i % 1000 == 0: print i
        add_to_tree(tree, s[i:])
    return tree

def substring_counts_helper(tree):
    '''Yields (substring, count, leaf), where leaf is a bool indicating
    whether the substring was from a leaf (i.e. a suffix). Multiple
    entries might be returned when one occurrence of a substring is a
    leaf and the other is not. In this case, you should take the
    latter count, from the non-leaf.'''
    if len(tree) == 1:
        yield (tree[0], 1, True)
        raise StopIteration
    total = 0
    for branch in tree[1:]:
        for s, cnt, leaf in substring_counts_helper(branch):
            yield (tree[0] + s, cnt, leaf)
            if leaf: total += cnt  # only count leaves
    if tree[0]:
        yield (tree[0], total, False)

def substring_counts(tree):
    '''Returns a list of (substring, count) for all substrings in the
    tree.'''
    result = {}
    for s, cnt, leaf in substring_counts_helper(tree):
        result[s] = cnt
    return result.items()

##################

input_str = sys.stdin.read()
print 'length:', len(input_str)
print

x = filter(lambda c: c != ' ', input_str)
print len(set(x)), 'unique characters:'
all_counts(x)
print

x = [input_str[i:i+2] for i in range(len(input_str)-1)]
x = filter(lambda c: ' ' not in c and '\n' not in c, x)
print len(set(x)), 'unique bigrams:'
top_counts(x)
print

x = [input_str[i:i+3] for i in range(len(input_str)-2)]
x = filter(lambda c: ' ' not in c and '\n' not in c, x)
print len(set(x)), 'unique trigrams:'
top_counts(x)
print

x = input_str.replace('\n',' ').split(' ')
x = filter(bool, x)
print len(set(x)), 'unique words:'
top_counts(x, padding=10)
print

print 'longest repeated substrings:'
tree = suffix_tree(input_str)
substrings = substring_counts(tree)
substrings = filter(lambda (s, cnt): s == s.strip(), substrings)
substrings = filter(lambda (s, cnt): cnt > 1 and len(s) > 3, substrings)
substrings.sort(key=lambda (s, cnt): -len(s) + 1.0 / cnt)
prev_substrings = []
for i in range(len(substrings)):
    s, cnt = substrings[i]
    if True not in [s in prev_s and cnt == prev_cnt for (prev_s, prev_cnt) in prev_substrings]:
        print repr(s), cnt, '#' * cnt
        prev_substrings.append((s, cnt))

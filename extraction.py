#!/usr/bin/python -u
#
# http://tools.qhex.org/

from pprint import pprint as pp
import time
import sys
import bisect
# import dictionary (below)

def p(x):
    widths = [0] * max(map(len, x))
    for row in x:
        for c, val in enumerate(row):
            widths[c] = max(widths[c], len(str(val)))
    for row in x:
        print ' '.join(map(lambda val, width: str(val).center(width),
                           row, widths))

# tables are a dictionary from a tuple of elements to a label:
#
# joe fred mike sam => NAME
# 2   3    5    2   => NUMBER

verbose = False

alphabet = 'abcdefghijklmnopqrstuvwxyz'

NUM_ROUNDS = 4

# unary operations
ops1 = {}
ops1['int'] = lambda x: int(x)
ops1['sub1'] = lambda x: x-1
ops1['add1'] = lambda x: x+1
#ops1['neg'] = lambda x: -x
ops1['len'] = lambda x: len(x)
ops1['chr'] = lambda x: alphabet[x-1] if x > 0 else FAIL
ops1['alpha'] = lambda x: ''.join(c for c in x if c.lower() in alphabet)
ops1['mod10d'] = lambda x: x % 10 if x >= 0 else FAIL
ops1['mod26'] = lambda x: x % 26 if x >= 0 else FAIL
ops1['mod100'] = lambda x: x % 100 if x >= 0 else FAIL
def op_rot(x):
    assert len(x) == 1
    i = alphabet.find(x.lower())
    return alphabet[i:] + alphabet[:i]
#ops1['rot'] = op_rot

# binary operations
ops2 = {}
ops2['index'] = lambda a,b: a[b-1] if b > 0 else FAIL
ops2['if'] = lambda a,b: b if {0:False, 1:True, '0':False, '1':True}[a] else ''
#ops2['sum'] = lambda a,b: int(a)+int(b)
#ops2['mod'] = lambda a,b: a % b

# these operations must have some arguments satisfying these conditions
op_input = {}
op_input['mod10d'] = lambda x: x > 10
op_input['mod26'] = lambda x: x > 26
op_input['mod100'] = lambda x: x > 100

# these operations must produce some results satisfying these conditions
op_output = {}
op_output['len'] = lambda x: x > 1
op_output['alpha'] = lambda x: len(x) > 1

for x in op_input.keys() + op_output.keys():
    assert x in ops1 or x in ops2  # operations from op_input and op_output must exist

# make sure operations don't conflict with each other
for a in ops1.keys() + ops2.keys():
    for b in ops1.keys() + ops2.keys():
        if a != b and a in b:
            raise Exception('conflicting operations: ' + a + ' ' + b)

def apply_op1(name, op, table, row):
    '''Apply a unary operation to a row of the table.'''
    # check input restrictions
    if name in op_input and \
            sum(map(lambda x: x != '!' and x != '?' and op_input[name](x),
                    row)) < 3:
        return False
    new_row = []
    errors = 0
    for x in row:
        if x == '?':
            new_row.append('?')
            continue
        try:
            assert x != '!'
            y = op(x)
        except Exception:
            y = '!'
        if y == '!':
            errors += 1
        new_row.append(y)
    # check output restrictions
    new_row_vals = filter(lambda x: x != '?', new_row)
    if name in op_output and sum(map(op_output[name], new_row_vals)) < 3:
        return False
    return try_append(table, new_row, name + '(' + table[row] + ')')

def apply_op2(name, op, table, row1, row2):
    '''Apply a binary operation to two rows of the table.'''
    # check input restrictions
    if name in op_input and \
            sum(map(lambda a,b:
                        a != '!' and a != '?' and \
                        b != '!' and b != '?' and \
                        op_input[name](a, b),
                    row1, row2)) < 3:
        return False
    elts = len(row1)
    new_row = []
    errors = 0
    for i in range(elts):
        if row1[i] == '?' or row2[i] == '?':
            new_row.append('?')
            continue
        try:
            assert row1[i] != '!'
            assert row2[i] != '!'
            y = op(row1[i], row2[i])
        except Exception:
            y = '!'
        if y == '!':
            errors += 1
        new_row.append(y)
    # check output restrictions
    new_row_vals = filter(lambda x: x != '?', new_row)
    if name in op_output and sum(map(op_output[name], new_row_vals)) < 3:
        return False
    return try_append(table, new_row, name + '(' + table[row1] + ', ' + table[row2] + ')')

import dictionary

DICT_MULTIPLIER = [0, 0.6, 0.7, 0.75, 0.8, 1.0]

def find_word(word):
    '''Looks up a word and returns a dictionary multiplier if there is a
    match, or 0 if not found. Also handles wildcards.'''
    i = word.find('?')
    if i == -1:
        return DICT_MULTIPLIER[dictionary.score(word)]
    best_result = 0
    for c in alphabet:
        new_word = word[:i] + c + word[i+1:]
        result = find_word(new_word)
        if result == 1:
            return result
        if result and (result < best_result or best_result == 0):
            best_result = result
    return best_result

word_score_cache = {}
def word_score(answer):
    '''Returns a score for the answer and a list of lengths indicating how
    it breaks down into words.'''
    global word_score_cache
    if answer == '': return 0, []
    if answer in alphabet or answer in alphabet[::-1]:
        return 0, [len(answer)]
    if answer in word_score_cache:
        return word_score_cache[answer]
    best_lengths = []
    best_score = -999
    for i in range(1, len(answer)+1):
        word = answer[:i].lower()
        word_value = -2  # penalty for all words
        dict_result = find_word(word)
        if dict_result:
            # word value depends on length and dictionary multiplier
            word_value += len(word)**1.5 * dict_result
        next_score, next_lengths = word_score(answer[i:])
        score = word_value + next_score
        lengths = [len(word)] + next_lengths
        if score > best_score:
            best_lengths = lengths
            best_score = score
    if len(word_score_cache) > 10000:
        word_score_cache = {}
    word_score_cache[answer] = (best_score, best_lengths)
    return best_score, best_lengths

def split_words(s, lengths):
    result = []
    for x in lengths:
        result.append(s[:abs(x)])
        s = s[abs(x):]
    return ' '.join(result)

def derivation_score(derivation):
    '''Returns a numerical penalty for the complexity of a derivation.'''
    operations = derivation.count('(')
    arguments = derivation.count(',')
    return 0 - operations - arguments - 0.1*len(derivation)

def overall_score(answer, derivation):
    '''Returns a score for an answer/derivation and its word breakdown.'''
    w_score, w_breakdown = word_score(answer)
    d_score = derivation_score(derivation)
    return w_score - 3*len(answer) + d_score*0.5, w_breakdown

def try_append(table, row, label, force=False):
    '''Append the row to the table. Returns true if a change was made.
    If a row already exists with the same data, but the new row has a
    shorter description, then only the description is modified.'''
    if not force:  # see if row looks okay
        if row.count('!') > 1:  # at most one error
            return False
        values = set(filter(lambda x: x != '' and x != '?', row))
        if len(values) < 3 and values != set((False,True)):  # at least 3 unique values
            return False
    row = tuple(row)
    if row in table and derivation_score(label) <= derivation_score(table[row]):
        return False  # don't add the row if an equivalent row with better score exists
    table[row] = label
    if verbose:
        print ','.join(map(str, row)), '--', label
    return True

def transpose(table):
    height, width = len(table), len(table[0])
    return [[table[r][c] for r in range(height)] for c in range(width)]

orderings = {}  # dict from order to derivation
def add_order(row, label):
    row_vals = filter(lambda x: x != '?', row)
    if len(row_vals) < 4: return
    if len(set(row_vals)) < len(row_vals): return  # do not sort if there are duplicates
    if '!' in row: return  # do not sort if there are errors

    def orders_with_unknowns(row):
        '''Yields tuples indicating the possible sortings for the row given
        unknowns.'''
        def insertions(lst, elts):
            '''Yields lst with elts inserted at every position.'''
            if not elts:
                yield lst
            else:
                for i in range(len(lst)):
                    new_lst = lst[:]
                    new_lst.insert(i, elts[0])
                    for option in insertions(new_lst, elts[1:]):
                        yield option
        known = [(row[i], i) for i in range(len(row)) if row[i] != '?']
        known.sort()
        known = [i[1] for i in known]
        unknown = [i for i in range(len(row)) if row[i] == '?']
        for option in insertions(known, unknown):
            yield tuple(option)
    for x in orders_with_unknowns(row):
        if x not in orderings or \
                derivation_score(label) > derivation_score(orderings[x]):
            orderings[x] = label
        x = tuple(reversed(x))
        if x not in orderings or \
                derivation_score(label + ' reversed') > derivation_score(orderings[x]):
            orderings[x] = label + ' reversed'

def take_top(n):
    '''Reduces the number of orderings to the top N by score.'''
    ord_lst = orderings.items()
    ord_lst.sort(key=lambda (k,v): derivation_score(v))
    orderings = dict(ord_lst[:n])

def sortings(row):
    '''Yields all available orderings of the given row, with label.'''
    results_seen = {}  # cache of result -> score
    for order in orderings:
        result = tuple(row[i] for i in order)
        label = orderings[order]
        score = derivation_score(label)
        if result in results_seen and score <= results_seen[result]:
            continue
        results_seen[result] = score
        yield result, label

update_time = time.time()
def need_update():
    global update_time
    if time.time() - update_time > 30:
        update_time = time.time()
        return True
    return False

def solve(raw_table):
    '''Find extractions for a table, where each column is a category of data.
    For example:
    [['JELLO', 5],
    ['HARRY', 1],
    ['FOWL', 4],
    ['FOLLOW', 3],
    ['RELATE', 2]]'''
    global orderings
    start_time = time.time()

    # check input
    assert len(raw_table) > 1
    for row in raw_table[1:]:
        if len(row) != len(raw_table[0]):
            print '\n'.join([','.join(r) for r in raw_table])
            print
            print 'Error: inconsistent number of values at row:'
            print ','.join(row)
            sys.exit()

    for row in raw_table:
        for elt in row:
            if elt != '?' and '?' in elt:
                print '\n'.join([','.join(r) for r in raw_table])
                print
                print 'Error: "?" must not appear with other characters in element:'
                print elt
                sys.exit()
            if '!' in elt:
                print '\n'.join([','.join(r) for r in raw_table])
                print
                print 'Sorry, input must not contain "!".'
                sys.exit()

    # create the table
    table = {}
    for c in range(len(raw_table[0]))[::-1]:
        label = 'c' + str(c + 1)
        table[tuple(row[c] for row in raw_table)] = label

    # add a row for i = 0..n
    try_append(table, range(1,len(raw_table)+1), 'i', True)

    # print with sorted columns
    p(transpose(sorted([[table[x]] + list(x) for x in table],
                       key=lambda row: 0 if row[0] == 'i' else int(row[0][1:]))))
    print

    num_wildcards = sum([row.count('?') for row in raw_table])
    if num_wildcards == 1:
        print '1 wildcard'
    elif num_wildcards > 1:
        print num_wildcards, 'wildcards'

    # add more seed constants
    try_append(table, range(len(raw_table), 0, -1), '-i', True)
    max_val = apply(max, [apply(max, map(lambda x: len(x) if type(x) is str else 0, row))
                          for row in table])
    for i in range(max_val):#range(-max_val,max(max_val,26)):
        try_append(table, (i,) * len(raw_table), str(i), True)

    #### try all operations
    changes = True
    round_num = 0
    while changes and round_num < NUM_ROUNDS:
        changes = False
        round_num += 1
        table_rows = table.keys()
        # Try unary operations on every row
        for row in table_rows:
            for name, op in ops1.iteritems():
                if name + '(' in table[row]:  # do not repeat operations
                    continue
                if apply_op1(name, op, table, row):
                    changes = True
        # Try binary operations on every pair of rows
        for row1 in table_rows:
            for row2 in table_rows:
                if row1 == row2: continue
                for name, op in ops2.iteritems():
                    if name + '(' in table[row1]: continue  # do not repeat operations
                    if name + '(' in table[row2]: continue
                    if apply_op2(name, op, table, row1, row2):
                        changes = True
        print 'round', round_num, '-', len(table), 'lists'

    #### collect orderings
    orderings = {}
    for row in table:
        add_order(row, table[row])
    # try pairs of simple rows
    for row1 in table:
        for row2 in table:
            if row1 == row2: continue
            if table[row1].count('(') > 0: continue
            if table[row2].count('(') > 0: continue
            #if table[row1][0] not in ('c','i'): continue
            #if table[row2][0] not in ('c','i'): continue
            add_order(map(lambda a,b: (a,b), row1, row2),
                      '(%s,%s)' % (table[row1],table[row2]))
    num_orderings = len(orderings)
    print num_orderings, 'orderings'
    #take_top(100)
    #if len(orderings) == num_orderings:
    #    print num_orderings, 'orderings'
    #else:
    #    print len(orderings), '/', num_orderings, 'orderings'

    # filter table
    # each row must have one element that is a single character
    for row in table.keys():
        if True not in [c in row or c.upper() in row for c in alphabet]:
            del table[row]
    print len(table), 'values'

    # get answer estimates
    sorted_count = 0
    resolved_count = 0
    for row in table:
        for row_sorted, sort_label in sortings(row):
            sorted_count += 1
            resolved_count += 26 ** row_sorted.count('?')
    print sorted_count, 'guesses'
    if sorted_count != resolved_count:
        print '%dx wildcard multiplier' % (resolved_count / sorted_count)

    #### compute answers
    answers = []
    num_answers = 0
    scoring_start_time = time.time()
    for row in table:
        for row_sorted, label in sortings(row):
            answer = ''.join(map(str, row_sorted))
            derivation = table[row] + ' sorted by ' + label
            score, breakdown = overall_score(answer, derivation)
            bisect.insort(answers, (-score, answer, breakdown, derivation))
            num_answers += 1
            if need_update():
                est = (time.time() - scoring_start_time) * (sorted_count - num_answers) / num_answers
                est = round(est / 60)
                est = '(~%i min)' % est if est >= 1 else ''
                print '%.1f%%' % (100.0 * num_answers / sorted_count), est
            if len(answers) > 100:
                answers = answers[:50]
    printed = set()
    print
    for score, answer, breakdown, derivation in answers:
        if answer not in printed:
            print split_words(answer, breakdown), '--', derivation#, '--', -score
            printed.add(answer)
            if len(printed) > 30:
                break
    print
    t = time.time() - start_time
    if t >= 120:
        print int(t/60), 'minutes', int(t%60), 'seconds'
    else:
        print t, 'seconds'

x = sys.stdin.read()
if '\t' in x:
    x = [row.split('\t') for row in x.split('\n') if row.strip()]
else:
    x = [row.split(',') for row in x.split('\n') if row.strip()]
x = [[elt.strip() for elt in row] for row in x]
solve(x)

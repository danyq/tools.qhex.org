#!/usr/bin/python -u
#
# http://tools.qhex.org/
#
# Converts to and from various encodings.
#
# All encoding functions are tried on the input, then the results are
# scored and printed. Results are de-duped to show only one variation
# of a given encoding, and results with too many errors or too little
# information are suppressed.
#
# An 'encoder' is an arbitrary function from str->str.
#
# The encoder name need not be unique. If a '~' is present in the
# name, only the portion before the '~' is considered for de-duping
# purposes, but the full name (without the '~') is printed in the
# results.
#
# In the result, a '?' is considered an error. Results with too many
# errors are not printed.

import sys
import os
import base64
import re

CMUDICT = '../dict/cmudict.0.7a'  # relative to program location

input_str = sys.stdin.read().replace('\t',' ').strip()
input_str = '\n'.join([line.strip() for line in input_str.split('\n')])

encoders = []  # list of (name, function)

def add_encoder(name, func, binary_symbols=None):
    '''Adds an encoder to the system.
    name: name of encoding
    func: str->str encoding function
    If binary_symbols are provided, then also adds versions of the
    encoder that recognize inputs with an alphabet of two characters,
    and replace those characters with the binary symbols when calling
    the function.'''
    encoders.append((name, func))
    if binary_symbols is None: return
    assert len(binary_symbols) == 2
    def new_func(input_str, func, binary_symbols):
        input_chars = set(input_str)
        if len(input_str) < 10: return None  # too small
        if input_chars >= set(binary_symbols): return None  # already uses binary symbols
        if len(input_chars - set(' \n')) != 2: return None  # must have alphabet of two chars
        char_a, char_b = tuple(input_chars - set(' \n'))
        return func(''.join(map(lambda c: binary_symbols[0] if c == char_a else \
                                    binary_symbols[1] if c == char_b else c,
                                input_str)))
    encoders.append((name, lambda input_str: new_func(input_str, func=func, binary_symbols=binary_symbols)))
    encoders.append((name, lambda input_str: new_func(input_str, func=func, binary_symbols=binary_symbols[::-1])))

def is_numeric(input_str):
    return len(set(input_str) & set('1234567890')) > 0 and set(input_str) <= set('1234567890abcdef .-+=*,/?\n')

def check_redundancy(input_str):
    '''Returns True if the input is non-numeric and does not have too many
    repeating characters.'''
    if len(input_str) < 10: return True
    if is_numeric(input_str): return False
    return len(set(input_str) - set(' \n')) > 2

def elt_map(func, input_str):
    '''Map func over space or comma-delimited elements of input, concatenating the results.'''
    return '\n'.join([''.join(map(func, filter(bool, re.split(' |,|, ', line))))
                      for line in input_str.split('\n')])

def add_seq_decoding(name, chunk_sizes, func, binary_symbols=None):
    '''Adds an encoding based on a function that takes a list of strings
    and decodes the elements into characters. chunk_sizes is a list of
    lengths to attept dividing the input into.'''
    for chunk_size in [0] + chunk_sizes:
        def chunk_f(s, chunk_size, func):
            if len(s) == 0: return ''
            if chunk_size == 0: return func([s])
            return func([s[i:i+chunk_size]
                         if len(s[i:i+chunk_size]) == chunk_size else '?'
                         for i in range(0,len(s),chunk_size)])
        add_encoder(name, lambda input_str, chunk_size=chunk_size, func=func: \
                        '\n'.join([''.join(map(lambda s: chunk_f(s, chunk_size, func),
                                               filter(bool, re.split(' |,|, ', line))))
                                   for line in input_str.split('\n')]),
                    binary_symbols)
        # also try concatenating the input lines (with a penalty)
        add_encoder(name, lambda input_str, chunk_size=chunk_size, func=func: \
                        chunk_f(input_str.replace('\n','').replace(' ',''), chunk_size, func) + \
                        '\n' * sum(map(lambda c: c=='\n', input_str)),
                    binary_symbols)

def add_char_encoding(name, func):
    '''Adds an encoding based on a function that transforms a single
    character into a longer encoded form.'''
    def f(input_str, func):
        if not check_redundancy(input_str): return None
        return '\n'.join([' '.join(map(func, line)) for line in input_str.split('\n')])
    add_encoder(name, lambda input_str: f(input_str, func=func))

def add_char_decoding(name, chunk_sizes, func, binary_symbols=None):
    '''Adds an encoding based on a function that takes a string and
    decodes it into a single character. chunk_sizes is a list of
    lengths to attept dividing the input into.'''
    add_seq_decoding(name, chunk_sizes, lambda x: ''.join(map(func, x)), binary_symbols)

###############

def toval(c):
    return ' ABCDEFGHIJKLMNOPQRSTUVWXYZ'.find(c.upper())
def tochar(n):
    return ' ABCDEFGHIJKLMNOPQRSTUVWXYZ'[n]

def try_chr(x, base=10):
    try: c = chr(int(x, base))
    except: return '?'
    if '\\' in repr(c) and c != '\\': return '?'
    return c
def try_int(x, base=10):
    try: return int(x, base)
    except: return '?'

add_char_encoding('letter~ decimal', lambda c: str(toval(c)).replace('-1','?'))
add_char_decoding('letter~ decimal', [2], lambda c: tochar(int(c)) \
                      if set(c) <= set('0123456789') and int(c) <= 26 \
                      else '?' * ((len(c)+1)/2))
add_char_decoding('letter~ binary', [5], lambda s: tochar(int(s,2)) \
                      if set(s) <= set('01') and int(s,2) <= 26 else '?', '01')
add_char_decoding('letter~ ternary', [3], lambda s: tochar(int(s,3)) \
                      if set(s) <= set('012') and int(s,3) <= 26 else '?')

add_char_encoding('ascii', lambda c: bin(ord(c))[2:].rjust(7,'0'))
add_char_decoding('ascii', [7,8], lambda c: try_chr(c, 2), '01')
add_char_decoding('ascii~ octal', [3], lambda c: try_chr(c, 8))
add_char_decoding('ascii~ decimal', [2,3], lambda c: try_chr(c, 10))
add_char_decoding('ascii~ hex', [2], lambda c: try_chr(c, 16))

# removed these encodings to simplify output
#add_char_encoding('letter binary', lambda c: bin(toval(c))[2:].rjust(5,'0') \
#                      if toval(c) != -1 else '?????')
#add_char_encoding('ascii decimal', lambda c: str(ord(c)))
#add_char_encoding('ascii hex', lambda c: hex(ord(c))[2:].rjust(2,'0'))
#add_char_encoding('ascii binary', lambda c: bin(ord(c))[2:].rjust(7,'0'))

def to_binary(n):
    try: return bin(int(n))[2:] + ' '
    except: return '? '
add_encoder('binary', lambda input_str: elt_map(to_binary, input_str))
def from_binary(n):
    try: return str(int(n, 2)) + ' '
    except: return '? '
add_encoder('binary', lambda input_str: elt_map(from_binary, input_str))
def to_hex(n):
    try: return hex(int(n))[2:].rstrip('L') + ' '
    except: return '? '
add_encoder('hex', lambda input_str: elt_map(to_hex, input_str))
def from_hex(n):
    try: return str(int(n, 16)) + ' '
    except: return '? '
add_encoder('hex', lambda input_str: elt_map(from_hex, input_str))

###############

def ebcdic(x, base=2):
    try: c = chr(int(x, base)).decode('EBCDIC-CP-CH')
    except: return '?'
    if '\\' in repr(c) and c != '\\': return '?'
    return c
add_char_decoding('ebcdic', [8], lambda c: ebcdic(c, 2), '01')
add_char_decoding('ebcdic~ decimal', [3], lambda c: ebcdic(c, 10))
add_char_decoding('ebcdic~ hex', [2], lambda c: ebcdic(c, 16))

def bacon(x):
    try: return 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[int(x, 2)]
    except: return '?'
add_char_decoding('bacon cipher', [5], bacon, '01')

ustty_ltrs = '\x00E\nA SIU\rDRJNFCKTZLWHYPQOBG`MXV`'
ustty_figs = '\x003\n- \x0787\r$4\',!:(5")2#6019?&`./;`'

def decode_ustty_vals(vals):
    letters = True
    result = ''
    for x in vals:
        if x == 31: letters = True
        elif x == 27: letters = False
        elif x < 0 or x >= 32: result += '?'
        elif letters: result += ustty_ltrs[x]
        else: result += ustty_figs[x]
    if result == '': return '?'
    return result.encode('string_escape')
def ustty(symbols, base=2):
    vals = []
    for x in symbols:
        try: vals.append(int(x, base))
        except: vals.append(-1)
    return decode_ustty_vals(vals)
add_seq_decoding('ustty', [5], lambda x: ustty(x, 2), '01')
add_seq_decoding('ustty~ decimal', [2], lambda x: ustty(x, 10))
add_seq_decoding('ustty~ hex', [2], lambda x: ustty(x, 16))

def tapcode(val):
    val = filter(lambda c: c in 'abcdefghijklmnopqrstuvwxyz0123456789', val)
    if len(val) != 2: return '?'
    if val[0] not in '12345' or val[1] not in '12345': return '?'
    x = (int(val[0])-1)*5 + int(val[1]) - 1
    return 'ABCDEFGHIJLMNOPQRSTUVWXYZ'[x]
add_char_decoding('tap code', [2], tapcode)

def tapcode_dot(val):
    if any(c not in '.-' for c in val): return '?'
    if val.count('-') != 1: return '?'
    a, b = val.split('-')
    return tapcode([str(len(a)), str(len(b))])
add_encoder('tap code', lambda input_str: elt_map(tapcode_dot, input_str), '.-')
add_encoder('tap code', lambda input_str: ''.join(map(tapcode_dot, input_str.split('--'))))

###############

keypad = ' 22233344455566677778889999'
def to_keypad(c):
    if c == '\n': return '\n'
    i = toval(c)
    return '?' if i == -1 else keypad[i]
add_encoder('phone keypad', lambda input_str: ''.join(map(to_keypad, input_str)))

###############

# todo: incorporate the 'uppercase' symbol?
# for now, braille conversions ignore case
br_c = " abcdefghijklmnopqrstuvwxyz'.,;!-:?"
br = '''\
  x x xxxxx xxxxx  x xx x xxxxx xxxxx  x xx x  xxxxxx                 
    x    x xx xxxxx xx  x    x xx xxxxx xx  x xx   x x  xxx x xx  xxx 
                      x x x x x x x x x x xxxx xxxxxxxx  x  x x xx  xx'''
br = br.replace(' ','`').replace('x','#')
br = map(list, br.split('\n'))
braille = {}
from_braille = {}
for i, c in enumerate(br_c):
    symbol = tuple((br[r][i*2],br[r][i*2+1]) for r in range(3))
    braille[c] = symbol
    from_braille[symbol] = c

def to_braille(c):
    if c.lower() in braille:
        return braille[c.lower()]
    else:
        return (('?','?'),('?','?'),('?','?'))

def braille_f(input_str):
    if not check_redundancy(input_str): return None
    result_lines = []
    for line in input_str.split('\n'):
        if len(line) > 0:
            result_line = map(to_braille, line)
            result_line = '\n'.join(['  '.join(map(lambda x: ' '.join(x[r]), result_line))
                                     for r in range(3)])
            result_lines.append(result_line)
    return '\n\n'.join(result_lines)
add_encoder('braille', braille_f)

def from_braille_f(x):
    result = ''
    for r in range(0, len(x), 3):
        for c in range(0, len(x[r]), 2):
            if r+3 > len(x) or c+2 > len(x[r]):
                result += '?'
                continue
            symbol = tuple(tuple(x[r+i][c:c+2]) for i in range(3))
            result += from_braille.get(symbol, '?')
        result += '\n'
    return result.upper()
add_encoder('braille', lambda input_str: from_braille_f(map(list, filter(bool, input_str.replace(' ','').split('\n')))), '`#')

##############
morse_c = 'abcdefghijklmnopqrstuvwxyz'
morse = '.- -... -.-. -.. . ..-. --. .... .. .--- -.- .-.. -- -. --- .--. --.- .-. ... - ..- ...- .-- -..- -.-- --..'
morse_c += '0123456789'
morse += ' ----- .---- ..--- ...-- ....- ..... -.... --... ---.. ----.'
morse_c += '.,?\'!/()&:;=+-_"$@'
morse += ' .-.-.- --..-- ..--.. .----. -.-.-- -..-. -.--. -.--.- .-... ---... -.-.-. -...- .-.-. -....- ..--.- .-..-. ...-..- .--.-.'
morse = morse.split(' ')
assert len(morse) == len(morse_c)
morse_table = {}
from_morse_table = {}
for i in range(len(morse)):
    morse_table[morse_c[i]] = morse[i]
    from_morse_table[morse[i]] = morse_c[i]
def to_morse(c):
    if c == ' ': return ' '
    if c.lower() in morse_c:
        return morse_table[c.lower()]
    return '???'
add_char_encoding('morse code', to_morse)

def from_morse_f(input_str):
    result = elt_map(lambda c: from_morse_table[c].upper() if c in from_morse_table else '?', input_str)
    if set(result) <= set('ET\n'):  # degenerate case for binary
        return None
    return result
add_encoder('morse code', from_morse_f, '.-')

#############
keyboard_lower = '''\
`1234567890-=
qwertyuiop[]\\
asdfghjkl;'
zxcvbnm,./'''
keyboard_upper = '''\
~!@#$%^&*()_+
QWERTYUIOP{}|
ASDFGHJKL:"
ZXCVBNM<>?'''
keyboard_lower = keyboard_lower.split('\n')
keyboard_upper = keyboard_upper.split('\n')
def print_keyboard(s, keymaps):
    #result = map(list, keyboard_lower)
    result = [['`']*13, ['`']*13, ['`']*11, ['`']*10]
    for c in s:
        for row in range(4):
            for keyboard in keymaps:
                x = keyboard[row].find(c)
                if x != -1:
                    result[row][x] = '#'
    return ' '.join(result[0]) + '\n' + \
        '   ' + ' '.join(result[1]) + '\n' + \
        '    ' + ' '.join(result[2]) + '\n' + \
        '     ' + ' '.join(result[3])
def qwerty_f(input_str):
    if is_numeric(input_str): return None
    if sum(map(lambda c: c in ''.join(keyboard_lower+keyboard_upper), set(input_str))) < 4:
        return None
    return '\n\n'.join(map(lambda line: print_keyboard(line, (keyboard_lower, keyboard_upper)),
                           filter(bool, input_str.split('\n'))))
add_encoder('qwerty keyboard', qwerty_f)

dv_keyboard_lower = '''\
`1234567890[]
',.pyfgcrl/=\\
aoeuidhtns-
;qjkxbmwvz'''
dv_keyboard_upper = '''\
~!@#$%^&*(){}
"<>PYFGCRL?+|
AOEUIDHTNS_
:QJKXBMWVZ'''
dv_keyboard_lower = dv_keyboard_lower.split('\n')
dv_keyboard_upper = dv_keyboard_upper.split('\n')
def dvorak_f(input_str):
    if is_numeric(input_str): return None
    if sum(map(lambda c: c in ''.join(dv_keyboard_lower+dv_keyboard_upper), set(input_str))) < 4:
        return None
    return '\n\n'.join(map(lambda line: print_keyboard(line, (dv_keyboard_lower, dv_keyboard_upper)),
                           filter(bool, input_str.split('\n')))) + ' '  # tiebreak output length with qwerty
add_encoder('dvorak keyboard', dvorak_f)

#############

def to_base26(s):
    s = s.lower()
    if not set(s) <= set('abcdefghijklmnopqrstuvwxyz'): return '??? '
    x = map(lambda (i,c): (toval(c)-1)*pow(26,len(s)-1-i), enumerate(s))
    return str(sum(x)) + ' '
add_encoder('base 26', lambda input_str: elt_map(to_base26, input_str) if check_redundancy(input_str) else None)

def base(x, n):
    """Convert integer x to base n.  Returns a list of digits,
    with the most significant digit first."""
    quot, rem = divmod(x, n)
    if quot == 0:
        return [rem]
    return base(quot, n) + [rem]
def from_base26(s):
    try: x = int(s)
    except: return '??? '
    if x < 0: return '??? '
    return ''.join(map(lambda i: tochar(i+1), base(x, 26))) + ' '
def from_base26_f(input_str):
    result = elt_map(from_base26, input_str)
    if set(result) <= set('AB \n'):  # degenerate case for binary
        return None
    return result
add_encoder('base 26', from_base26_f)

##############

def try_f(f, *extra_args):
    '''Makes f (string->string) into a function which returns '?' upon any error.
    If provided, extra_args are also passed to f.'''
    def g(f, *args):
        try:
            result = apply(f, args)
        except Exception:
            return '?'
        return ''.join([c if '\\' not in repr(c) or c in '\\\n\r\t' else '?'
                        for c in result])
    return lambda x: g(f, x, *extra_args)

add_encoder('base64', try_f(base64.b64decode))
add_encoder('base32', try_f(base64.b32decode, True))

##############

periodic = '''\
H ` ` ` ` ` ` ` ` ` ` ` ` ` ` ` ` He
Li Be ` ` ` ` ` ` ` ` ` ` B C N O F Ne
Na Mg ` ` ` ` ` ` ` ` ` ` Al Si P S Cl Ar
K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Ge As Se Br Kr
Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe
Cs Ba Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn
Fr Ra Lr Rf Db Sg Bh Hs Mt Ds Rg Cn Uut Fl Uup Lv Uus Uuo
` ` ` ` ` ` ` ` ` ` ` ` ` ` ` ` ` `
` ` La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu `
` ` Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No Lr `'''
periodic = map(lambda s: s.split(' '), periodic.upper().split('\n'))

periodic_w = '''\
1 ` ` ` ` ` ` ` ` ` ` ` ` ` ` ` ` 2
3 4 ` ` ` ` ` ` ` ` ` ` 5 6 7 8 9 10
11 12 ` ` ` ` ` ` ` ` ` ` 13 14 15 16 17 18
19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36
37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54
55 56 71 72 73 74 75 76 77 78 79 80 81 82 83 84 85 86
87 88 103 104 105 106 107 108 109 110 111 112 113 114 115 116 117 118
` ` ` ` ` ` ` ` ` ` ` ` ` ` ` ` ` `
` ` 57 58 59 60 61 62 63 64 65 66 67 68 69 70 71 `
` ` 89 90 91 92 93 94 95 96 97 98 99 100 101 102 103 `'''
periodic_w = map(lambda s: s.split(' '), periodic_w.upper().split('\n'))

pt_height = len(periodic)
pt_width = len(periodic[0])

elt_to_weight = {}
weight_to_elt = {}
for r in range(pt_height):
    for c in range(pt_width):
        if periodic[r][c] == '`': continue
        elt_to_weight[periodic[r][c]] = periodic_w[r][c]
        weight_to_elt[periodic_w[r][c]] = periodic[r][c]

add_encoder('atomic weight', lambda input_str: elt_map(lambda n: weight_to_elt[n] if n in weight_to_elt else '?', input_str))

elements_by_size = elt_to_weight.keys()
elements_by_size.sort(key=len, reverse=True)
def pt_split(s):
    if s == '': yield []
    for elt in elements_by_size:
        if s.startswith(elt):
            for rest in pt_split(s[len(elt):]):
                yield [elt] + rest

def weight_f(input_str):
    result = ''
    for line in input_str.replace(' ','').upper().split('\n'):
        try:
            parsed = pt_split(line).next()
        except:
            result += '?' * len(line) + '\n'
            continue
        for elt in parsed:
            result += elt_to_weight[elt] + ' '
        result += '\n'
    return result
add_encoder('atomic weight', weight_f)

def periodic_f(input_str):
    result = ''
    for line in filter(bool, input_str.replace(' ','').upper().split('\n')):
        try:
            parsed = pt_split(line).next()
        except:
            result += '?' * len(line) * 2 + '\n\n'
            continue
        table = [['  ' if periodic[r][c] == '`' else '` '
                  for c in range(pt_width)] for r in range(pt_height)]
        for elt in parsed:
            for r in range(pt_height):
                for c in range(pt_width):
                    if periodic[r][c] == elt:
                        table[r][c] = elt[-2:][0] + elt[-2:][1:].lower().ljust(1)
        result += '\n'.join([''.join(row) for row in table]) + '\n\n'
    return result
add_encoder('periodic table', periodic_f)

####################

# http://www.bennetyee.org/ucsd-pages/area.html
area_codes = '''\
201 NJ,202 DC,203 CT,204 MB,205 AL,206 WA,207 ME,208 ID,209 CA,210 TX,212 NY,\
213 CA,214 TX,215 PA,216 OH,217 IL,218 MN,219 IN,224 IL,225 LA,226 ON,228 MS,\
229 GA,231 MI,234 OH,236 BC,239 FL,240 MD,248 MI,250 BC,251 AL,252 NC,253 WA,\
254 TX,256 AL,260 IN,262 WI,267 PA,269 MI,270 KY,276 VA,278 MI,281 TX,283 OH,\
289 ON,301 MD,302 DE,303 CO,304 WV,305 FL,306 SK,307 WY,308 NE,309 IL,310 CA,\
312 IL,313 MI,314 MO,315 NY,316 KS,317 IN,318 LA,319 IA,320 MN,321 FL,323 CA,\
325 TX,330 OH,331 IL,334 AL,336 NC,337 LA,339 MA,340 VI,341 CA,347 NY,351 MA,\
352 FL,360 WA,361 TX,369 CA,380 OH,385 UT,386 FL,401 RI,402 NE,403 AB,404 GA,\
405 OK,406 MT,407 FL,408 CA,409 TX,410 MD,412 PA,413 MA,414 WI,415 CA,416 ON,\
417 MO,418 QC,419 OH,423 TN,424 CA,425 WA,430 TX,431 MB,432 TX,434 VA,435 UT,\
438 QC,440 OH,442 CA,443 MD,450 QC,464 IL,469 TX,470 GA,475 CT,478 GA,479 AR,\
480 AZ,484 PA,501 AR,502 KY,503 OR,504 LA,505 NM,506 NB,507 MN,508 MA,509 WA,\
510 CA,512 TX,513 OH,514 QC,515 IA,516 NY,517 MI,518 NY,519 ON,520 AZ,530 CA,\
539 OK,540 VA,541 OR,551 NJ,557 MO,559 CA,561 FL,562 CA,563 IA,564 WA,567 OH,\
570 PA,571 VA,573 MO,574 IN,575 NM,580 OK,585 NY,586 MI,587 AB,601 MS,602 AZ,\
603 NH,604 BC,605 SD,606 KY,607 NY,608 WI,609 NJ,610 PA,612 MN,613 ON,614 OH,\
615 TN,616 MI,617 MA,618 IL,619 CA,620 KS,623 AZ,626 CA,627 CA,628 CA,630 IL,\
631 NY,636 MO,639 SK,641 IA,646 NY,647 ON,650 CA,651 MN,657 CA,660 MO,661 CA,\
662 MS,669 CA,670 MP,671 GU,678 GA,679 MI,681 WV,682 TX,689 FL,701 ND,702 NV,\
703 VA,704 NC,705 ON,706 GA,707 CA,708 IL,709 NL,712 IA,713 TX,714 CA,715 WI,\
716 NY,717 PA,718 NY,719 CO,720 CO,724 PA,727 FL,731 TN,732 NJ,734 MI,737 TX,\
740 OH,747 CA,754 FL,757 VA,760 CA,762 GA,763 MN,764 CA,765 IN,769 MS,770 GA,\
772 FL,773 IL,774 MA,775 NV,778 BC,779 IL,780 AB,781 MA,785 KS,786 FL,787 PR,\
801 UT,802 VT,803 SC,804 VA,805 CA,806 TX,807 ON,808 HI,810 MI,812 IN,813 FL,\
814 PA,815 IL,816 MO,817 TX,818 CA,819 QC,828 NC,830 TX,831 CA,832 TX,835 PA,\
843 SC,845 NY,847 IL,848 NJ,850 FL,856 NJ,857 MA,858 CA,859 KY,860 CT,862 NJ,\
863 FL,864 SC,865 TN,867 YT,870 AR,872 IL,878 PA,901 TN,902 NS,903 TX,904 FL,\
905 ON,906 MI,907 AK,908 NJ,909 CA,910 NC,912 GA,913 KS,914 NY,915 TX,916 CA,\
917 NY,918 OK,919 NC,920 WI,925 CA,927 FL,928 AZ,931 TN,935 CA,936 TX,937 OH,\
939 PR,940 TX,941 FL,947 MI,949 CA,951 CA,952 MN,954 FL,956 TX,957 NM,959 CT,\
970 CO,971 OR,972 TX,973 NJ,975 MO,978 MA,979 TX,980 NC,984 NC,985 LA,989 MI'''
area_code_map = {}
for entry in area_codes.split(','):
    code, region = entry.split(' ')
    area_code_map[code] = region
add_char_decoding('area code', [3], lambda x: area_code_map[x] if x in area_code_map else '?')


############################

# http://www.airportcodes.org/
airports = '''\
A:ACAEAGALANAQARATAYBABDBEBIBJBKBLBMBQBRBSBTBVBXBZCACCCECHCICKCTCVDADBDDDEDJDKDLDQDUDZEOEPERESETEXEYFAFTGAGBGDGEGFGHGJGLGNGPGRGSGTGUGVHBHNHOHUIAICIMINITIUIYJAJFJIJLJRJUKAKBKFKIKJKLKNKPKSKUKVKXKYLBLCLFLGLJLMLOLPLSLWLYMAMDMHMIMMMOMQMSMVMYNCNENFNGNINKNMNRNUNVNXOIOJOKOLOOOROTPFPLPNPOPWQGQIQJQPRCRDRHRIRKRMRNRPRRRTRURWSBSDSESFSJSMSOSPSRSUSVSWTCTDTHTKTLTMTNTQTWTYTZUAUCUGUHUKULUPUQURUSUUUXUYVIVLVNVPWDWZXAXDXKXMXPXTYQYTYWZBZDZNZOZR
B:AHAKALAQASAUAVAXAYBABIBKBMBNBOBUCACDCICLCNCOCQDADBDDDHDJDLDODPDQDSDUEBEDEGEHEIEJELENEOERESETEUEWEYFDFFFLFNFQFSFVGAGFGIGMGOGRGYHBHDHEHGHHHIHJHKHMHOHQHRHSHUHVHXHYIAIDIIIKILIMIOIQIRISJAJBJFJIJLJMJRJVJXJZKAKCKIKKKOKQKSKWKXKZLALELFLGLILJLKLLLRLTLVLZMAMDMEMIMKMOMPMUMVMYNANDNENJNKNNNPNSNXNYOAOBOCODOGOHOIOJOMONOOOSOVOXPFPNPSPTPXPYQHQKQLQNQSRARCRDRERIRKRLRMRNRORQRRRSRTRURWSASBSCSDSKSLSOTHTITJTKTMTRTSTTTUTVUAUCUDUFUIUOUQURUSUZVAVBVCVEVGVHVIWAWDWEWGWIWKWNWQWTXBXDXMXRXUXZYAYMYUZEZGZIZLZNZOZRZV
C:ACAEAGAIAKALANAPAQASAWAYAZBBBEBGBHBLBOBQBRCFCJCKCMCPCRCSCUCVDBDCDGDRDVEBECEDEEEGEIEKEMENEQEZFAFEFNFRFSFUGAGBGDGHGIGKGNGOGPGQGRGXGYHAHCHGHIHOHPHQHSHTHUHXHYIAICIDIFIJIKIPITIUIWIXJAJBJCJJJLJSJUKBKGKIKOKSKXKYLDLELJLLLMLOLPLQLTLYMAMBMEMFMGMHMIMJMKMNMUMWMXNBNCNDNFNJNKNMNPNQNSNXNYOCODOGOKOROSOUPCPDPEPHPIPOPQPRPTPVRDRIRLRPRVRWSGSISTSYTATCTDTGTLTMTNTSTUUCUEULUMUNUPUQURUUUWUZVCVGVJVLVMVNVOVQVUWAWBWLXBXHXJYBYFYIYOYSZEZHZLZMZNZSZX
D:ABACADAMARAUAVAXAYBMBOBQBTBVCACFCMDCDIDMEAECELEMENEREZFWGAGEGOGTHNIBIEIJIKILINIRIUIYJBJEJGJJJNKIKRLALCLGLHLMLULYMDMEMMMUNDNHNKNMNRNZOBODOGOHOKOLOMOUPLPOPSRBRGRHRORSRWSESKSMTDTMTTTWUBUDUJUMUQURUSUTVLVOWBXBYGYRYUZA
E:AEAMARASATAUBABBBDBJBOBUCNDADIDLDODREKENFLGCGEGLGMGNGOGSHLHMIBINISJAJHKOLCLDLELFLHLILMLPLQLSLULVMAMDMKMNMOMSMXNANENFNHNTNUNYOHOIPLPRPSQSRCRFRIRZSBSCSLSMSRTHTZUEUGUNUXVEVGVNVVWEWIWRXMXTYLYPYWZEZS
F:AEAIAJAOARATAVAYBMCODEDFDHEGENEZGIIEIHIZJRKBKLKQKSLALFLGLLLNLOLRLWMAMONANCNINJNLNTOCODOEOGORPORARCRERORSRURWSCSDSMSPTATUUEUGUJUKUNUTWAYVZO
G:AFAJANAOARAUAXBEBLCCCICKCMCNDEDLDNDQDTDVDXDZEAEBEGELEOERESETEVFFFKFNGGGNGSGTGWHAHBHEHTIBICIGILISIZJAJLJTKALALFLHLILTLVMBMPNBNDNUNVOAOBOEOHOIOJONOQOROTOVPAPNPSPTPZRBRIRJRLRORQRRRURWRXRYRZSESOSPSTTETFTOTRUAUBUCUDUIUMUPURUWVAVRWDWLWTWYXFYAYEYLYMYNYYZAZMZOZT
H:AAACADAEAHAJAKAMANAPAQASAUAVBABBBECQCRDBDFDNDSDYEHELERETEXFAFEFNFSFTGAGDGHGLGNGRGUHHHNHQIBIDIIIJILINIRISITIWJRKBKDKGKKKNKTKYLDLFLHLNLZMEMOMVNANDNHNLNMNSODOEOFOGOKOMONOQOROTOUOVPAPBPHPNRBRERGRKRLROSLSNSVTATITNTRTSUFUHUIUNUQUSUUUVUXUYVAVBVGVNVRWNYAYDYGYLYNYSZG
I:AAADAHAMANARASBEBZCICNCTDADNDREGEVFJFNFOFPGAGGGMGRGUHUKOKSKTLALELFLILMLOLPLYMFMPMTNANCNDNGNLNNNUNVNXOAOMOPOSPAPEPHPIPLPNPTQMQQQTRARCRGRJRKSASBSCSGSNSPSTTBTHTKTMTOUEULVAVCVLVRWDWJXAXBXCXEXJXLXMXRXSXUXZYKZOZT
J:ACAGAIALANAQATAVAXBRCACKCRCUDFDHDODZEDEGEJERFKFRGAGCGNGRHBHEHGHMHQHSHWIBIJIMINIWJNJUKGKRLNMKMOMSMUNBNNNSNUNZOEOGOIONPAPRQERHROSISMSRSTSUTRUIUJULUVUZVAVLYV
K:AAABACAEAGAJALANAOATAWAXBCBFBLBMBPBRBTBVBXCCCDCFCGCHCLCMCQCZDDDIDLDMDOEFEKEWGDGKGLGXHIIFINIVIXKHKIKULGLLLWMONKNWOAOTPBPCPNPVQARKSMTBTDTMTNTPTRTSTTTWUAUDUFUGUHUKULUNUOUQUSUTUVUYVAVBVCVDVGVLWAWEWFWGWIWJWKWLWMWNWTWYXAXKYAYUYXYZZFZN
L:ABADAEAFAIAJANAOAPAQARASAUAWAXBABBBCBDBEBFBJBLBPBSBUBVBWCACECGCHCYDBDCDEDHDIDUDYEAEBEDEHEIEJEQERETEVEXFTFWGAGBGGGIGKGLGPGQGSGWHEHGHRHWIFIGIHIIIKILIMINIRISITJGJUKAKBKEKLKNKOLALILWMAMLMMMNMPMTNBNENKNONSNVNYNZODOFOHONOSOVPAPBPIPLPMPPPQPSPUPYRDRERHRMRTSASCSESISPSTSYTDTKTNTOTQTTUAUCUDUGUMUNUPUQURUVUWUXVIVOWBWKWNWOWSWTWYXAXGXRXSYAYCYGYIYPYRYSYUZCZHZOZR
M:AAABADAFAGAHAJAKAMANAOAQARASATAUAVAYAZBABEBHBJBLBSBTBXCECGCHCICKCMCNCOCPCTCVCWCXCYCZDCDEDGDHDJDKDLDPDQDSDTDUDWDYDZECEDEEEHEIELEMESEUEXFAFEFFFGFJFMFOFRFUGAGBGFGHGLGMGQGSGTGWGZHDHGHHHKHPHQHTHUHXIAIDIIIJIKIMIRISJAJBJDJEJFJKJLJMJNJTJVJZKEKGKKKLKMKQKRKSKTKUKWKYKZLALBLELHLILLLMLNLSLULXLYMBMDMEMGMJMKMOMXMYNBNCNFNGNINJNLNRNTNUNYOAOBOCODOFOIOLONOQOTOUOVOWOZPAPBPKPLPMPNPWQFQLQNQTQXRARDRERSRURVRYRZSASESJSLSNSOSPSQSRSSSTSUSYTFTJTMTRTSTTTVTYUAUBUCUEUHUKUNURUXUZVBVDVRVSVYWAWEWFWHWZXHXLXMXPXSXTXXXZYAYCYDYEYGYIYJYRYTYUYWYXYYZGZIZLZOZTZV
N:AAAGAJAKALANAOAPASATAWBOBXCACECLCNCUCYDBDGDIDJDKDMDRDYDZEGEREVFGFOGBGEGIGOGSGXHAHVIBICIMIXJCKCKDKGKILALDLFLGLKLPMAMEMGNBNGNLNMNTNXNYOBOCOJOSOUOZPEPLQNQYRDRKRLRTSBSKSNSTTETGTITLTNTOTTTYUBUEUIULUPUSUXVAVKVRVTWIYCYKYMYNYU
O:AGAJAKAXBDBOBUCJDNDSDYERESFKGGGNGSGXGZHDHOIMIRITKAKCKDKJKLKQKRKULBLJLPMAMBMDMEMHMOMRMSNDNGNINTNXOKOLOMPOPURBRDRFRGRHRKRLRNRTRVRWRYSASDSHSISKSLSRSWSYSZTDTHTMTPTUTZUAUDULUZVBVDWBXBXRYAYEZHZZ
P:ACADAFAHAJAKAPARATAZBCBDBEBHBIBJBMBOBPBZCACHCLDBDGDLDPDSDTDXECEEEGEIEKEMENERESETEUEWEXFBFNFOGAGFGKGVGXHBHCHEHFHLHOHSHWHXIAIBIDIEIFIHIKIPIRISITIUIXIZJGJMKAKBKCKNKRKUKYKZLBLHLJLMLNLOLPLQLSLULVLWLZMAMCMFMGMIMLMOMQMRMVMWMYMZNANCNDNHNINKNLNPNQNRNSNZOAOGOLOMOPOROSOTOUOZPBPGPPPSPTPVPWQCQIQMQQQSRARCRGRHRNRQRSSASCSESGSISMSOSPSRSSSUSYSZTATFTGTHTJTPTUTYUBUDUFUGUJUQUSUTUWUYVCVDVGVHVKVOVRWMWQXMXOXUYEYHYJZBZEZHZOZU
Q:BCBFCEDUFKFZJYJZKBKLKSQPROWFWMWYXGYW
R:ABAEAHAIAJAMAOAPARASATAZBABEBHBJBPBRBVBYCBCECHCMCQCUDDDEDGDMDUDVDZECEGELENEPESETEUEXFPGAGLGNHIHOIAIBICIGIKISIWIXIYJHJKJNKDKSKTLGMAMIMPNBNENJNLNNNONPNSOAOBOCOKOMOPOROSOTOVOWOYPMPNRGRSSASDSHSJSTSUSWTBTMTWUAUHUNURUTVAVDVKVN
S:AFAHAIALANAPATAVBABNBPBSBYCCCECKCLCMDFDLDPDQEAELEZFOGFGNGUGYHDHGHHHRHVHXINITJCJDJOJTJUKBKGKKKPLCLELKLNLPLQLULWLXLYLZMAMFMIMKMLMRMSMXNANENNNONPNWOCODOFOGOIOJONOOOPOUOYPCPIPNPSPUQGQHQORERGRQRVSASGSHSRTBTCTDTGTITLTMTNTOTRTSTTTWTXUBUFUJULUNURUVUXVAVBVCVDVGVJVLVOVQVSVUVXVZWAWDWFWGXBXFXKXLXMXPXRYDYMYOYQYRYUYXYYYZZDZGZKZMZTZXZZ
T:ABACAEAHAIALAMAOAPARASATBGBIBJBNBOBPBSBTBUBZCACBCGCHCLCOCPCQCTDBDDEEEHEKERETEUEXEZFFFIFNFSGDGGGHGJGMGNGOGUGZHEHFHGHLHNHOHRHSHUIAIDIEIFIHIJIMINIPIQIRISIUIVIYIZJAJIJMJQJSKAKBKEKGKJKKKNKQKSKULCLELHLLLMLNLSLTLVMCMGMHMJMMMPMRMSMTMUMWMXNANCNGNKNNNONRNXOBODOEOFOGOHOLOMOSOUOVOWOYPAPEPPPQPRPSRARCRDRERFRGRIRKRNRORSRURVRWRZSASBSESFSJSMSNSOSRSTSVTBTETJTNTQTSTTTUUAUBUCUFUGUIUJUKULUNUOUPURUSUUUVVAVCVFVUVYWAWBWFWUXGXKXLXMXNYFYNYOYRYSZAZNZX
U:AKAQASBABBBJBPCACTDIDJDRELEOETFAGBGCGUIBIHIIIKINIOIPITJEKKLALBLDLILNLPLULYMDMENGNKNNPGPNRARCRGRJRORTRURYSHSKSLSMSNTHTKTNTOTPTTUAUDUSVEVFVLYLYN
V:AAAGAIAKANAOARASATAVAWBVBYCDCECPCTDADBDCDEDMDSDZEEELEREYFAGOHMIEIGIIIJILISITIVKGKOKTLCLDLGLILKLLLNLSLVMEMUNONSNXOGOHOZPNPSQSRARKRNSASGSTTBTETZUPVBVIVOXCXEXO
W:AAAEAGAIAMAQASATAWBABBBQBUDGEDEHEIETFIGAGEGPHFHHHKICILINJAJUKAKJKKLGLHLKLSMAMEMHMKMNMOMPMRMXNANNNPNRNSNZOTPBRERGRLRORYSNSRSTSUSXSZTATETKTLTOTSUDUGUHUNUSUUVBVKVNWKWPWTXNYAYNYS
X:ADAKAPAWAXAZBEBRCHCICMDBDDDGDHDLDMDPDQDSDUDVDWDXDYDZEAECEEEFEGEHEJEKELEMEREYFCFEFGFKFLFMFNFQFSFVFWFYGJGKGRGYHHHMHSIAIBICIDIFIIILIMIOIPIYJLJQKHKSKVLBLJLKLMLQLVLYLZMHMNMSMYNANNOPPBPKPNPXPZQPQURPRYSCSHSISPTGTLTYUZVSVVWAWYYAYDZBZCZL
Y:AAABACAGAIAKAMAOAPATAXAYAZBBBCBEBGBIBKBLBPBRBSBTBVBXBZCACBCCCDCGCKCMCOCRCSCYDADFDIDNDPDQEGEKEREVFAFBFCFHFJFOFSFXFZGBGHGJGKGLGOGPGRGTGVGWGXGZHAHBHDHGHIHKHMHOHPHRHYHZIFIHIKINIOIVIWJTKAKFKGKLKMKQKSKTKULCLDLELHLLLQLRLWMHMMMOMQMTMXMYNANBNCNENGNJNLNONSNTNZOCOGOHOJOOOPOWPAPBPCPEPFPHPJPLPMPNPOPRPWPXPYPZQBQCQDQGQIQKQLQMQNQQQRQTQUQXQYQZRARBRFRGRJRLRSRTSBSFSGSHSJSKSLSMSOSRSTSYTATDTETFTHTLTQTSTZUBUDULUMUTUXUYVBVCVMVOVPVQVRVZWBWGWHWJWKWLWMWPWRXCXEXHXJXKXLXNXPXSXTXUXXXYYBYCYDYEYFYGYHYJYQYRYTYUYYYZZFZGZRZSZTZV
Z:ACADAGAHALAMAQATAYAZBBBFBJBQBRBVBYCODHDJDNEGELEMFDFNGCGIGSGUHAHOHQIDIHJNKBKEKGLNLOLTNANENZPBQNRFRHRIRJRKRMSASESJTBTHTMUHUMVAVKWLWSXMYLYRZU'''
airport_set = set()
for line in airports.split('\n'):
    a,rest = line.split(':')
    for i in range(0, len(rest), 2):
        airport_set.add(a+rest[i]+rest[i+1])
add_char_decoding('airport code', [3], lambda x: x.upper()+' ' if x.upper() in airport_set else '??? ')


##########################

# Apply every encoder, rejecting results if they have too many '?'s
# or not enough content.
encoder_results = []
for enc_name, enc_f in encoders:
    result = enc_f(input_str)
    #print enc_name, repr(result)
    if result is None or len(result.strip()) == 0:
        continue
    if len(filter(lambda c: c == '?', result)) * 2 > len(filter(lambda c: c not in '\n ', result)):
        continue  # too many unknowns
    if '?' in result and len(set(result) - set('? \n')) == 1:
        continue  # only one symbol, degenerate
    encoder_results.append((enc_name, result))

if len(encoder_results) == 0:
    print 'no encodings found'
    sys.exit()

# sort by length and quality of result
def result_score(r):
    '''lower is better'''
    return len(r.split('\n')) * 40 + len(r) + sum(map(lambda c: c == '?', r)) * 4

encoder_results.sort(key=lambda (n,r): result_score(r))

printed_scores = {}  # name -> score
printed_results = set()

for enc_name, enc_result in encoder_results:
    name = enc_name.strip()
    base_name = name.split('~')[0]  # used for deduping
    print_name = name.replace('~','')  # used for display
    result_strip = enc_result.strip()
    if base_name in printed_scores and printed_scores[base_name] < result_score(enc_result):
        continue  # only print one result for a given name, unless tied
    if result_strip in printed_results:
        continue  # duplicate result
    printed_scores[base_name] = result_score(enc_result)
    printed_results.add(result_strip)
    print print_name + ':'
    print result_strip
    print



###########################################
# prununciation is computed separately


alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

dictionary = {}
here = os.path.dirname(__file__)
f = open(os.path.join(here, CMUDICT))
for line in f:
    if line[0] not in alphabet:
        continue
    word, pron = line[:-1].split('  ')
    pron = pron.replace(' ', '-')
    if '(' in word:  # this is an alternate pronunciation
        word = word.split('(')[0]
        if len(pron) >= len(dictionary[word]):
            continue  # always take the shorter one
    dictionary[word] = pron

# Split the input into a 2D array of tokens, where each word is a token
# and any non-letter characters (including spaces) appear as a token as well.
text_words = []
for line in input_str.split('\n'):
    result = []
    word = ''
    for c in line.upper() + ' ':  # extra space to get last word
        if c in alphabet + "'":
            word += c
            continue
        if word:
            result.append(word)
            word = ''
        result.append(c)
    text_words.append(result[:-1])

# if not enough valid words, exit here
text_words_flat = reduce(lambda a,b: a+b, text_words)
if sum(word[0] in alphabet and word in dictionary
       for word in text_words_flat) < len(text_words_flat)/2:
    sys.exit()

total = 0
exact = True
for line in text_words:
    for word in line:
        if word[0] in alphabet:
            if word in dictionary:
                total += sum([c in '012' for c in dictionary[word]])
            else:
                exact = False
print 'total syllables:', str(total) + ('?' if not exact else '')
print

print 'syllables per word:'
for line in text_words:
    for word in line:
        if word[0] in alphabet:
            if word in dictionary:
                print sum([c in '012' for c in dictionary[word]]),
            else:
                print '?',
    print
print

def vowel(part):
    return True in [c in '012' for c in part]

print 'syllable breakdown:'
for line in text_words:
    result = []
    for word in line:
        if word[0] not in alphabet:
            result.append(word)
            continue
        if word not in dictionary:
            result.append('[%s?]' % word)
            continue
        pron = dictionary[word]
        # if one syllable word, don't change it
        if sum([c in '012' for c in pron]) <= 1:
            result.append(word)
            continue
        parts = pron.split('-')
        # progressively attach consonants to vowels:
        # V C C => V-C C
        # first in a series of consonants gets attached to previous vowel
        new_parts = []
        for part in parts:
            new_parts.append(part)
            if len(new_parts) >= 3 and \
                    new_parts[-3][-1] in '012' and \
                    not vowel(new_parts[-2]) and \
                    not vowel(new_parts[-1]):
                new_parts[-3:] = [new_parts[-3] + new_parts[-2], new_parts[-1]]
        parts = new_parts
        # C * => C-*
        # consonants get attached to whatever is after them
        new_parts = []
        for part in parts:
            new_parts.append(part)
            if len(new_parts) >= 2 and not vowel(new_parts[-2]):
                new_parts[-2:] = [new_parts[-2] + new_parts[-1]]
        parts = new_parts
        # V C => V-C
        # attach trailing consonants
        new_parts = []
        for part in parts:
            new_parts.append(part)
            if len(new_parts) >= 2 and \
                    vowel(new_parts[-2]) and \
                    not vowel(new_parts[-1]):
                new_parts[-2:] = [new_parts[-2] + new_parts[-1]]
        parts = new_parts
        result.append(filter(lambda c: c not in '012', '-'.join(parts)))
    print ''.join(result)

print
print 'full pronunciation:'
for line in text_words:
    result = []
    for word in line:
        if word[0] in alphabet:
            result.append(dictionary.get(word, '[%s?]' % word))
        else:
            result.append(word)
    print ''.join(result)

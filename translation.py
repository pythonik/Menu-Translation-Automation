#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
import sys
import itertools
import string
from collections import Counter
from functools import reduce
from random import shuffle

__author__ = 'Kun Su'
data_file = 'data.txt'
stop_words = ['in','with','and','by','this']
chinese_symbols = ['，', '。', '（', '）', '、','-','+','—',]
english_symbols = [',','.','\\','/','&','(',')',';','%','<','>','?','!','#']

show_translation = False

extremely_small_constant = 2.2250738585072014e-30
hexlow = u'\u4e00'
hexhigh = u'\u9fff'

is_chinese = lambda char: hexlow <= char <= hexhigh
join_list = lambda l1,l2:l1+l2

e2ctest = 'yu shiang shredded pork'
c2etest = '鱼香肉丝'

def trim_punc( text, english=False ):
    replace = ' ' if english else ''    
    return ''.join(list(
        map(lambda x: 
            x if (x not in english_symbols) and (x not in chinese_symbols) else replace,
        text.strip())))

def pre_process( file_name ):
    table = []
    with open(file_name, 'r') as data:
        for line in data:
            splitted = line.strip().split('\t')
            if len(splitted) > 1:
                eng = trim_punc(splitted[1].lower(), True)
                ch = trim_punc(splitted[0])
            else:
                eng = trim_punc(next(data).lower(), True)
                ch = trim_punc(splitted[0])
            stem = list(filter(lambda x:x not in stop_words, eng.split(' ')))
            table.append([stem, list(ch)])
    shuffle(table)
    validation = table[int(0.9*len(table)):] 
    train = table[:int(0.9*len(table))] 
    for tp in train:
        tp[0] = list(filter(lambda x:len(x)>0,tp[0]))
    return validation, train


def two_word_probs(menu, chinese=False):
    sp = ' '
    if chinese:
        sp = ''
    menu_text = list(map(lambda x:sp.join(x),menu))
    #print(menu_text)
    #sys.exit()
    word_probs_dict = {}
    word_count_dict = {}
    for sentence in menu:
        sentence_iter = iter(sentence)
        if len(sentence)%2 == 1:
            last = sentence[-1]
            sentence_iter = iter(sentence[:-1])
        for w1 in sentence_iter:
            word = w1+ sp + next(sentence_iter)
            word_probs_dict[word] = len(list(filter(lambda x: word in x,menu_text)))/len(menu_text)
            word_count_dict[word] = len(list(filter(lambda x: word in x,menu_text)))
    #print(sorted(word_count_dict.items(), key=lambda x:x[1]))
    return word_probs_dict,word_count_dict


def two_word_approach(original, train, english_menu, chinese_menu, 
            eword_list, cword_list, eword_count, cword_count, 
            eword_prob, cword_prob, english2chinese):
    sentence = list(filter(lambda w: w not in stop_words, 
                    original.lower().split(' '))) if not is_chinese(original[0]) else original
    sentence = list(map(lambda x:x.strip(), sentence))
    iter_sentence = iter(sentence)
    break_down = []
    sp = ''
    bsp = ' '
    el1 = 0
    el2 = 1
    word_count = cword_count
    word_prob = cword_prob
    if not english2chinese:
        sp = ' '
        bsp =''
        el1 = 1
        el2 = 0
        word_count = eword_count
        word_prob = eword_prob
    pre = ''
    # break orginal to 2 word combs 
    for w1 in iter_sentence:
        word = ''
        if len(pre) > 0:
            word = pre + w1
            break_down.append(word)
        w2 = next(iter_sentence, '')
        word = w1 + bsp + w2
        break_down.append(word)
        pre = w2
        #print(word)
        #sys.exit()
    translated = []
    for seg in break_down:
        two_word_occurence_for_seg = {}
        contains_seg = list(filter(lambda el: seg in bsp.join(el[el1]) , train))
        translation_contains_seg = list(map(lambda el: el[el2], contains_seg))
        if len(contains_seg) == 0:
            # if two does not work, fall back to use word by word
            translated = translated + word_by_word(seg,train, 
                english_menu, chinese_menu, 
                eword_list, cword_list, 
                eword_count, cword_count, 
                eword_prob, cword_prob)
            continue
        for t1 in translation_contains_seg:
            s_iter = iter(t1)
            if len(t1)%2 == 1:
                last = t1[-1]
                s_iter = iter(t1[:-1])
            for w1 in s_iter:
                word = w1+ sp + next(s_iter)
                v = two_word_occurence_for_seg.setdefault(word,1)
                if v >= 1:
                    two_word_occurence_for_seg[word] = v + 1
        given_seg_prob_of_two_word = {}
        for k,v in two_word_occurence_for_seg.items():
            given_seg_prob_of_two_word[k] = v/word_count.setdefault(k, 
                extremely_small_constant)*word_prob.setdefault(k, 
                extremely_small_constant)
        try:
            w,p = max(given_seg_prob_of_two_word.items(),key=lambda x:x[1])
            translated.append(w)
        except Exception as e:
            print('error', seg)
    if show_translation:
        print(str(original)+ ' to ' + str(translated))
    return translated
    
def word_by_word(original, train, english_menu, chinese_menu, 
            eword_list, cword_list, eword_count, cword_count, 
            eword_prob, cword_prob):
    sentence = list(filter(lambda w: w not in stop_words, 
                    original.lower().split(' '))) if not is_chinese(original[0]) else original
    sentence = map(lambda x:x.strip(), sentence)
    translated = []
    for o in sentence:
        if is_chinese(o):
            contains_o = list(filter(lambda el: o in el[1] , train))
            translation_contains_o = list(map(lambda el: el[0], contains_o))
            word_count = eword_count
            word_prob = eword_prob
        else:
            contains_o = list(filter(lambda el: o in el[0] , train))
            #print(train)
            translation_contains_o = list(map(lambda el: el[1], contains_o))
            word_count = cword_count
            word_prob = cword_prob
        try:
            combined_contains_o = reduce(join_list, translation_contains_o)
        except Exception as e:
            #print('unknown word',o)
            translated.append(o)
            continue
        
        wcount = Counter(combined_contains_o)
        given_o_prob_of_ws = {}
        for w,c in wcount.items():
            given_o_prob_of_ws[w] = (c/word_count[w])*word_prob[w]
        w,p = max(given_o_prob_of_ws.items(), key=lambda x:x[1])
        translated.append(w)
    if show_translation:
        print(str(original)+ ' to ' + str(translated))
    return translated

def attempt_improve(original, train, english_menu, chinese_menu, 
            eword_list, cword_list, eword_count, cword_count, 
            eword_prob, cword_prob):
    sentence = list(filter(lambda w: w not in stop_words, 
                    original.lower().split(' '))) if not is_chinese(original[0]) else original
    sentence = map(lambda x:x.strip(), sentence)
    translated = []
    for o in sentence:
        if is_chinese(o):
            contains_o = list(filter(lambda el: o in el[1] , train))
            translation_contains_o = list(map(lambda el: el[0], contains_o))
            word_count = eword_count
            word_prob = eword_prob
        else:
            contains_o = list(filter(lambda el: o in el[0] , train))
            #print(train)
            translation_contains_o = list(map(lambda el: el[1], contains_o))
            word_count = cword_count
            word_prob = cword_prob
        try:
            combined_contains_o = reduce(join_list, translation_contains_o)
        except Exception as e:
            #print('unknown word',o)
            translated.append(o)
            continue
        
        wcount = Counter(combined_contains_o)
        given_o_prob_of_ws = {}
        for w,c in wcount.items():
            given_o_prob_of_ws[w] = (c/word_count[w])*word_prob[w]
        w,p = max(given_o_prob_of_ws.items(), key=lambda x:x[1])
        translated.append(w)
    if show_translation:
        print(str(original)+ ' to ' + str(translated))
    return translated


def evaluation( corpus, english2chinese=True):
    evaluation, train = pre_process(corpus)
    evaluation_len = len(evaluation)
    train_len = len(train)
    print('total_dishes: %d, use %d for training: , %d for validation: ' % 
            (evaluation_len+train_len, train_len, evaluation_len)) 
    english_menu = list(map(lambda el:el[0], train))
    chinese_menu = list(map(lambda el:el[1], train))

    eword_list = reduce(join_list, english_menu)
    cword_list = reduce(join_list, chinese_menu)

    eword_count = Counter(eword_list)
    cword_count = Counter(cword_list)

    eword_prob = {w:c/len(eword_list) for w,c in eword_count.items()}
    cword_prob = {w:c/len(cword_list) for w,c in cword_count.items()}
    test1 = 0
    for (dish,t) in evaluation:
        if english2chinese:
            original = ' '.join(dish)
            sol = t
        else:
            original = ''.join(t)
            sol = dish
        ret = word_by_word(original,train, 
                english_menu, chinese_menu, 
                eword_list, cword_list, 
                eword_count, cword_count, 
                eword_prob, cword_prob)

        test = map(lambda w: w in sol, ret)
        if all(test):
            test1 +=1
        else:
            test1  = test1  + sum([0.1 for x in test if x == True])
    test5 = 0
    for (dish,t) in evaluation:
        original = ''.join(t)
        sol = dish
        ret = word_by_word(original,train, 
                english_menu, chinese_menu, 
                eword_list, cword_list, 
                eword_count, cword_count, 
                eword_prob, cword_prob)

        test = map(lambda w: w in sol, ret)
        if all(test):
            test5 +=1
        else:
            test5  = test5  + sum([0.1 for x in test if x == True])

    #update eword dictionary with frequent words
    eword_prob.update(two_word_probs(english_menu)[0])
    eword_prob.update(two_word_probs(english_menu)[1])
    cword_prob.update(two_word_probs(chinese_menu, True)[0])
    cword_prob.update(two_word_probs(chinese_menu)[1])
    test2 = 0
    for (dish,t) in evaluation:
        # english input
        ret = two_word_approach(' '.join(dish),train, 
                english_menu, chinese_menu, 
                eword_list, cword_list, 
                eword_count, cword_count, 
                eword_prob, cword_prob, True)
        test = map(lambda w: w in t, ret)
        if all(test):
            test2 = test2+1
        else:
            test2 = test2 + sum([0.1 for x in test if x == True])
        #print(ret, dish, t)
    
    test3 = 0
    for (dish,t) in evaluation:
        # chinese input
        ret = two_word_approach(''.join(t),train, 
                english_menu, chinese_menu, 
                eword_list, cword_list, 
                eword_count, cword_count, 
                eword_prob, cword_prob, False)
        
        test = map(lambda w: w in dish, ret)
        if all(test):
            test3 = test3+1
        else:
            test3 = test3 + sum([0.1 for x in test if x == True])
    
    test4 = 0
    for (dish,t) in evaluation:
        # chinese input
        ret = attempt_improve(''.join(t),train, 
                english_menu, chinese_menu, 
                eword_list, cword_list, 
                eword_count, cword_count, 
                eword_prob, cword_prob)
        
        test = map(lambda w: w in dish, set(ret))
        if all(test):
            test4 = test4+1
        else:
            test4 = test4 + sum([0.1 for x in test if x == True])
    
    print('word_by_word English to Chinese performance: %.3f' % test1)
    print('word_by_word Chinese to English performance: %.3f' % test5)
    print('two_word_approach English to Chinese performance: %.3f' % test2)
    print('two_word_approach Chinese to English performance: %.3f' % test3)
    print('Improved two_word_approach Chinese to English performance: %.3f' % test4)

def main():
    evaluation(data_file)
        
if __name__ == '__main__':
    main()

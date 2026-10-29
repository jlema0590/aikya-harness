"""Stable lexical ranking; a request need not be a contiguous symbol substring."""
import re

STOP = frozenset(('the','a','an','please','change','modify','method','class','function','el','la','de','en','modifica','cambia','metodo','clase'))


def terms(text):
    return set(re.findall(r'[\w]+', text.casefold())) - STOP


def rank(row, query):
    wanted = terms(query)
    name = row.get('name', '')
    tokens = terms(name+' '+row['path'])
    exact = int(name.casefold() in wanted)
    score = exact*100 + len(wanted & tokens)*10
    return (-score, row['path'], row.get('start_line', 1), name)

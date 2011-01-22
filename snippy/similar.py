# -*- coding: ascii -*-

import re
import string
import struct

from functools import partial
from hashlib import sha1

def bulk_compare(base_sn):
  import string
  from difflib import SequenceMatcher

  # You'd think the lambda in SequenceMatcher would allow us to use .text, but
  # no, it matches incorrectly without .unfscked_text()

  match_list = []
  sm = SequenceMatcher(lambda x: x in string.whitespace)
  sm.set_seq2(base_sn.unfscked_text())
  for snippet in snippets:
    if snippet is base_sn:
      continue

    sm.set_seq1(snippet.unfscked_text())

    for a, b, size in sm.get_matching_blocks():
      if size >= 60:
        yield a, b, size

def compare(snippet1, snippet2):
  import string
  from difflib import SequenceMatcher

  # You'd think the lambda in SequenceMatcher would allow us to use .text, but
  # no, it matches incorrectly without .unfscked_text()

  match_list = []
  sm = SequenceMatcher(lambda x: x in string.whitespace)
  sm.set_seq2(snippet1.unfscked_text())
  sm.set_seq1(snippet2.unfscked_text())

  for a, b, size in sm.get_matching_blocks():
    if size >= 60:
      yield a, b, size

def make_trans():
  chars = "\n" # These will be replaced with a space
  return string.maketrans(chars, " "*len(chars))

get_sentences = re.compile(r'[^.!?]+[.!?\n\t ]+"*').finditer
collapse_dup_spaces = partial(re.compile(r' +').sub, ' ')
trans = make_trans()

def get_sentence_hashes(text):
  sentence = ""
  for match in get_sentences(text.lower().encode('ascii', 'ignore')):
    sentence += match.group(0)
    if len(sentence) < 40:
      continue
    sans_punct = string.translate(sentence, trans, string.punctuation)
    raw_sent = collapse_dup_spaces(sans_punct).strip()
    yield struct.unpack("q", sha1(raw_sent).digest()[:8])[0]
    sentence = ""

hash_lookup = {}
def setup_similarity_hashes(snippets):
  """Must be called before any similarity comparisons can be made."""
  for sn in snippets:
    for int_hash in get_sentence_hashes(sn.text):
      # XXX: worth doing sys.maxint check?
      try:
        hash_lookup[int_hash].append(sn)
      except KeyError:
        hash_lookup[int_hash] = [sn]

def find_similar_snippets(text):
  similar = set()

  for int_hash in get_sentence_hashes(text):
    try:
      similar.update(hash_lookup[int_hash])
    except KeyError:
      pass

  return similar

def defer_update_similarity(snippet):
  similarity.set_text("  Similarity: <Checking...>")
  loop.set_alarm_in(0.1, update_similarity_callback, user_data=snippet)

def update_similarity_callback(loop, this_snippet):
  matches = find_similar_snippets(this_snippet.text)
  if matches:
    ss = "%d possible" % len(matches)
  else:
    ss = "No similar entries."
  similarity.set_text("  Similarity: %s" % ss)

  for other_snippet in matches:
    # TODO: change color
    for a, b, size in compare(this_snippet, other_snippet):
      text = snippet.unfscked_text()

      pre = text[:b]
      hilite = 'important', text[b:b+size]
      post = text[b+size:]

      body.set_text([pre, hilite, post])
      return # TODO: process more than one

def old_update_similarity_callback(loop, snippet):
  """Very slow!"""
  matches = [x for x in bulk_compare(snippet)]
  if matches:
    ss = ", ".join(str(match) for match in matches)
  else:
    ss = "No similar entries."
  similarity.set_text("  Similarity: %s" % ss)

  if matches:
    a, b, size = matches[0]
    text = snippet.unfscked_text()

    pre = text[:b]
    hilite = 'important', text[b:b+size]
    post = text[b+size:]

    body.set_text([pre, hilite, post])

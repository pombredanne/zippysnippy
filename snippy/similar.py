# -*- coding: ascii -*-

import re
import string
import struct

from difflib import SequenceMatcher
from functools import partial
from hashlib import sha1

import common

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
  # You'd think the lambda in SequenceMatcher would allow us to use .text, but
  # no, it matches incorrectly without .unfscked_text()

  sm = SequenceMatcher(lambda x: x in string.whitespace)
  sm.set_seq1(snippet1.unfscked_text().lower())
  sm.set_seq2(snippet2.unfscked_text().lower())

  for a, b, size in sm.get_matching_blocks():
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

def find_similar_snippets(snippet):
  similar = set()

  for int_hash in get_sentence_hashes(snippet.text):
    try:
      similar.update(hash_lookup[int_hash])
    except KeyError:
      pass

  try:
    similar.remove(snippet)
  except KeyError:
    pass

  return similar

def update_similarity_callback(loop, tui):
  this_snippet = tui.current_snippet

  if not hash_lookup:
    setup_similarity_hashes(common.snippets)

  matches = find_similar_snippets(this_snippet)
  if matches:
    ss = "%d similar entries" % len(matches)
  else:
    ss = "No similar entries."
  tui.similarity.set_text("  Similarity: %s" % ss)

  stop = 0
  body = []

  for other_snippet in matches:
    # TODO: change color

    post = this_snippet.unfscked_text()
    for a, b, size in compare(this_snippet, other_snippet):
      start = a - stop
      stop = start + size

      pre = post[:start]
      hilite = 'important', post[start:stop]
      body += [pre, hilite]

      post = post[stop:]

    tui.body.set_text(body + [post])
    return # TODO: process more than one

# -*- coding: ascii -*-

import re
import string
import struct

from difflib import SequenceMatcher
from functools import partial
from hashlib import sha1

import common

def compare(snippet1, snippet2):
  # TODO: convert punct and stuff to spaces with translate so it doesn't screw
  # up offsets
  sm = SequenceMatcher(lambda x: x in string.whitespace)
  sm.set_seq1(snippet1.unfscked_text().lower())
  sm.set_seq2(snippet2.unfscked_text().lower())

  # Note that the last block will always be of size 0
  for a, b, size in sm.get_matching_blocks():
    if size >= 5:
      yield a, size

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

# TODO: add entries to hash_lookup as they are snipped!
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
  ss = "  Similarity: %s" % ss
  tui.similarity.set_text(ss)

  for other_snippet in matches:
    # TODO: change color

    post = this_snippet.unfscked_text()
    tot_size = 0
    stop = 0
    body = []
    for a, size in sorted(compare(this_snippet, other_snippet)):
      tot_size += size

      start = a - stop
      stop = start + size

      pre = post[:start]
      hilite = 'similar', post[start:stop]
      body += [pre, hilite]

      post = post[stop:]

    tui.body.set_text(body + [post])
    tui.similarity.set_text(ss + ", about %d chars" % tot_size)
    return # TODO: process more than one

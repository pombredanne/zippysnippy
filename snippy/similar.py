# -*- coding: ascii -*-

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

def defer_update_similarity(snippet):
  similarity.set_text("  Similarity: <Checking...>")
  loop.set_alarm_in(0.1, update_similarity_callback, user_data=snippet)

def update_similarity_callback(loop, snippet):
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


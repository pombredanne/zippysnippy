#!/usr/bin/env python
# -*- coding: ascii -*-

DATA_DIRECTORY = "/home/bthomson/.snippets"
SEP="-"*77 + "\n"

import re
import os
import fcntl
import ast
import collections

from pprint import pformat
from datetime import datetime

LOCK_FILE_PATH = os.path.join(DATA_DIRECTORY, "_lock")
REVIEW_PRIORITY_FILE_PATH = os.path.join(DATA_DIRECTORY, "_review_priority")

has_subcategories = set()

def read_review_priorities():
  try:
    with open(REVIEW_PRIORITY_FILE_PATH) as f:
      return ast.literal_eval(f.read())
  except:
    return {}

def write_review_priorities(p):
  with open(REVIEW_PRIORITY_FILE_PATH, 'w') as f:
    f.write(pformat(p))

def write_to_one_file():
  return
  with open("single-file-output.txt", 'w') as f:
    for snippet in snippets.values():
      for param in ('read_count', 'category', 'added'):
        f.write("%s: %s\n" % (param, str(getattr(snippet, param))))
      f.write("*\n")
      f.write(snippet.text)
      f.write(SEP)

def write_to_category_files(categories, snippets, status=False):
  #counter = collections.Counter()

  for category in categories:
    try:
      with open(category_name_to_relative_path(category), 'w') as f:
        for snippet in snippets:
          if snippet.category != category:
            continue
          f.write("%s: %s\n" % ('read_count', snippet.read_count))
          f.write("%s: %s\n" % ('added', snippet.added))
          f.write("%s: %s\n" % ('last_read', snippet.last_read))
          try:
            f.write("%s: %s\n" % ('source', snippet.source))
          except AttributeError:
            pass # no source
          if snippet.flags:
            f.write("%s: %s\n" % ('flags', ",".join(snippet.flags)))
          if snippet.rep_rate != 5:
            f.write("%s: %s\n" % ('rep_rate', snippet.rep_rate))
          f.write("*\n")
          f.write(snippet.text.encode("UTF-8"))
          f.write(SEP)
          #counter['snippets'] += 1
    except IOError:
      if status:
        print "IOError!"
    #counter['categories'] += 1
    #if status:
    #  print "%d snippets in %d categories written." % (
    #    counter['snippets'], counter['categories']
    #  )


def relative_path_to_category_name(path):
  """
  >>> relative_path_to_category_name('bash/fin.txt')
  'bash/fin'

  >>> relative_path_to_category_name('bash/fin/fin.txt')
  'bash/fin'
  """
  # TODO: support paths with dots
  s = path.split('.')[0].replace("_", " ")
  path1, file_name = os.path.split(s)
  path2, dir = os.path.split(path1)
  if file_name == dir:
    # file with same name as enclosing dir gets cat path truncated
    cat_path = os.path.join(path2, dir)
    has_subcategories.add(cat_path)
  else:
    cat_path = os.path.join(path2, dir, file_name)
  return cat_path.replace("/", ".")

def category_name_to_relative_path(cn):
  path = cn.replace(".", "/")
  if cn in has_subcategories:
    path, file_name = os.path.split(path)
    if path:
      path = path + '/' + file_name + '/' + file_name
    else:
      path = file_name + '/' + file_name

  return path.replace(' ', '_') + ".txt"

def read_directory(dir):
  import os
  import glob

  for infile in glob.glob(os.path.join(dir, '*')):
    path, filename = os.path.split(infile)
    if filename.startswith("."):
      continue

    if filename.startswith("_"):
      continue

    if os.path.isdir(infile):
      for x in read_directory(infile):
        yield x
      continue

    with open(infile, 'r') as f:
      data = f.read().decode('UTF-8', 'ignore')
    entries = re.split(SEP, data)
    for entry in entries:
      params, _, text = entry.partition("\n*\n")
      if params:
        p_dict = {}
        for param in params.split("\n"):
          name, _, value = param.partition(": ")
          if name == "":
            pass
          elif name == "added":
            p_dict['added'] = datetime.strptime(value.strip(),
                                                         "%Y-%m-%d %H:%M:%S.%f")
          elif name == "last_read":
            try:
              last_read_time = datetime.strptime(value.strip(),
                                                          "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
              last_read_time = datetime.now()
            p_dict['last_read'] = last_read_time
          elif name == "read_count":
            p_dict['read_count'] = int(value)
          elif name == "source":
            p_dict['source'] = value
          elif name == "flags":
            p_dict['flags'] = value.split(',')
          elif name == "rep_rate":
            p_dict['rep_rate'] = int(value)
          else:
            raise Exception("Unknown property '%s'" % name)

        try:
          text = text.rstrip() + "\n"
          read_count = p_dict.get('read_count', 0)
          last_read = p_dict.get('last_read', None)
          flags = p_dict.get('flags', None)
          source = p_dict.get('source', None)
          category = relative_path_to_category_name(infile)
          rep_rate = p_dict.get('rep_rate', None)
          added = p_dict['added']
          yield (read_count, text, last_read, flags, source,
                 category, rep_rate, added)

        except KeyError:
          print "Required property not found"
          print entry
          sys.exit(1)

def read_category_files():
  import os
  os.chdir(DATA_DIRECTORY)

  for x in read_directory(''):
    yield x

def release_lock():
  pass
  #lock_file.close()
  #os.unlink(LOCK_FILE_PATH)

def acquire_lock():
  pass
  #global lock_file

  #lock_file = open(LOCK_FILE_PATH, 'w')

  # Doesn't work with NFS
  #fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)

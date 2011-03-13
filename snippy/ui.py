#!/usr/bin/env python
# -*- coding: ascii -*-

import urwid

class SelText(urwid.Text):
  """A selectable text widget. See urwid.Text."""

  def selectable(self):
    return True

  def keypress(self, size, key):
    return key # don't handle any keys


class JKListbox(urwid.ListBox):
  """Listbox that also scrolls itself on j and k keypresses"""

  def keypress(self, size, key):
    if key == "j":
      key = "down"
    elif key == "k":
      key = "up"

    return urwid.ListBox.keypress(self, size, key)

class PopupMenu(urwid.WidgetWrap):
  """
  Creates a popup menu on top of another BoxWidget.

  Derived from rbreu_menus.by Rebecca Breu
  https://excess.org/hg/urwid-contrib/file/4159c2278814/rbreu_menus.py

  Attributes:

  selected -- Contains the item the user has selected by pressing <RETURN>,
              or None if nothing has been selected.
  """

  selected = None

  def __init__(self, menu_list, default, pos, body, extra_width=0):
    """
    menu_list: a list of strings with the menu entries
    default: string for initially-selected entry
    pos: example: ('fixed right', 0, 'fixed bottom', 1)
    body: widget displayed beneath the message widget
    """

    fg, bg = 'menu', 'menuf'

    self._content = [urwid.AttrWrap(SelText(" " + w), None, bg)
               for w in menu_list]

    # Calculate width and height of the menu widget:
    height = len(menu_list)
    width = 0
    for entry in menu_list:
      if len(entry) > width:
        width = len(entry)

    # Create the ListBox widget and put it on top of body:
    self._listbox = urwid.AttrWrap(JKListbox(self._content), fg)

    xpos = pos[0], pos[1]
    ypos = pos[2], pos[3]

    overlay = urwid.Overlay(
      self._listbox, body, xpos, width + 2 + extra_width, ypos, height
    )

    urwid.WidgetWrap.__init__(self, overlay)

    # Move listbox selection to initially-selected entry
    for item in menu_list:
      if item == default:
        break
      # XXX does size parameter matter? I don't think it does
      self._listbox.keypress((10,10), 'down')

  def keypress(self, size, key):
    """<RETURN> key selects an item."""

    if key == "enter":
      widget, _ = self._listbox.get_focus()
      text, _ = widget.get_text()
      self.selected = text[1:] # Get rid of the leading space...

    return self._listbox.keypress(size, key)

digits = set('123456789')

class ReviewCatPopupMenu(PopupMenu):
  def __init__(self, review_priorities, *args):
    PopupMenu.__init__(self, *args, extra_width=2)

    self._settings = review_priorities

    # Add spacing; add default for any empty categories
    for w in self._content:
      key = w.text[1:]
      w.set_text("   " + key)
      self._settings[key] = self._settings.get(key, "5")

    self._update()

  def _update(self):
    for w in self._content:
      key = w.text[3:]
      w.set_text(" %s " % self._settings[key] + key)

  def keypress(self, size, key):
    """Number key sets item priority"""

    widget, _ = self._listbox.get_focus()
    lookup_key = widget.text[3:]

    if key in digits | set('x'):
      self._settings[lookup_key] = key
      self._update()
      return

    return self._listbox.keypress(size, key)

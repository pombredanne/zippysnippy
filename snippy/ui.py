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

  def __init__(self, menu_list, default, pos, body):
    """
    menu_list: a list of strings with the menu entries
    default: string for initially-selected entry
    pos: example: ('fixed right', 0, 'fixed bottom', 1)
    body: widget displayed beneath the message widget
    """

    fg, bg = 'menu', 'menuf'

    content = [urwid.AttrWrap(SelText(" " + w), None, bg)
               for w in menu_list]

    # Calculate width and height of the menu widget:
    height = len(menu_list);
    width = 0;
    for entry in menu_list:
      if len(entry) > width:
        width = len(entry)

    # Create the ListBox widget and put it on top of body:
    self._listbox = urwid.AttrWrap(JKListbox(content), fg)

    xpos = pos[0], pos[1]
    ypos = pos[2], pos[3]

    overlay = urwid.Overlay(
      self._listbox, body, xpos, width + 2, ypos, height
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
        (widget, foo) = self._listbox.get_focus()
        (text, foo) = widget.get_text()
        self.selected = text[1:] # Get rid of the leading space...

    return self._listbox.keypress(size, key)

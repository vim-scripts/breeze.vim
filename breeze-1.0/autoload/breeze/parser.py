# -*- coding: utf-8 -*-
"""
breeze.parser
~~~~~~~~~~~~~

Parser class definition.

The Parser is responsible for parsing the current buffer and generating
a DOM tree.
"""

import vim
import itertools

import breeze.utils.misc
import breeze.utils.settings

try:
    # python 3
    import html.parser as HTMLParser
except ImportError:
    import HTMLParser as HTMLParser


class Node(object):
    """Node definition."""

    def __init__(self, tag="", attrs=None, starttag_text="",
                 parent=None, start=None, end=None):
        self.tag = tag          # tag name
        self.starttag_text = starttag_text # raw starttag text
        self.attrs = attrs      # a dictionary {attr: value, ..}
        self.start = start      # a tuple (row, col)
        self.end = end          # a tuple (row, col)
        self.parent = parent    # a Node or None (if root)
        self.children = []      # a list of Nodes

    def __str__(self):
        return "<{0} start={1} end={2}>".format(
            self.tag, self.start, self.end)

    def __repr__(self):
        return "<{0} start={1} end={2}>".format(
            self.tag, self.start, self.end)

    def id(self):
        """Returns the id attribute."""
        return self.attrs.get("id", [])

    def classes(self):
        """Returns the class attribute."""
        classes = self.attrs.get("class")
        if classes:
            return classes.split()
        else:
            return []

class Parser(HTMLParser.HTMLParser):
    """Custom HTML parser."""

    def __init__(self):
        HTMLParser.HTMLParser.__init__(self)  # TODO: check with python 3

        # module reference shortcuts
        self.misc = breeze.utils.misc

        self.last_known_error = None
        self.success = False
        self.tree = Node(tag="root")
        self.stack = [self.tree]
        self.empty_tags = dict((k, True) for k in
            ["br", "base", "hr", "meta", "link", "base", "link",
            "source", "meta", "img", "embed", "param", "area", "col", "input",
            "command", "keygen", "track", "wbr"])

    def feed(self, buffer):
        """Generates a brand new tree at each call."""
        self.tree = Node(tag="root")
        self.stack = [self.tree]
        try:
            HTMLParser.HTMLParser.feed(self, "\n".join(buffer))
            self.success = True
            self.last_known_error = None
        except HTMLParser.HTMLParseError as e:
            self.last_known_error = dict(msg=e.msg, pos=(e.lineno, e.offset))
            self.tree = Node(tag="root")
            self.success = False
        else:
            self.close()
        self.reset()

    def handle_startendtag(self, tag, attrs):
        """Handles empty tags."""
        self.handle_starttag(tag, attrs, skip_emptytag_check=True)
        self.handle_endtag(tag)

    def handle_starttag(self, tag, attrs, skip_emptytag_check=False):
        """Handles the start of a tag.

        Note how this method handles empty tags. The HTMLParser does not
        recognize self-closing tags if they aren't closed with '../>',
        although this is totally acceptable in non-XHTML documents. So we call
        the handle_startendtag tags by ourselves and we make sure we don't run
        infinite recursive calls with the skip_emptytag_check parameter.
        """
        if not skip_emptytag_check and tag in self.empty_tags:
            self.handle_startendtag(tag, attrs)
            return

        if self.stack:
            node = Node(tag, dict(attrs), self.get_starttag_text(),
                        self.stack[-1], self.getpos())
            self.stack[-1].children.append(node)
            self.stack.append(node)

    def handle_endtag(self, tag):
        """Handles the end of a tag.

        If a script tag is opened, ignore all the junk in there until
        the tag is closed.
        """
        if self.stack:
            if self.stack[-1].tag == "script" and tag != "script":
                # ignore everything inside script tag
                return

            if tag != self.stack[-1].tag:
                # tag mismatch
                if any(n.tag == tag for n in self.stack):
                    msg = "no closing tag for '<{0}>'".format(
                        self.stack[-1].tag)
                    pos = self.stack[-1].start
                else:
                    msg = "no opening tag for '</{0}>'".format(tag)
                    pos = self.getpos()
                raise HTMLParser.HTMLParseError(msg, pos)

            self.stack[-1].end = self.getpos()
            self.stack.pop(-1)

    def get_current_node(self):
        """Searches for the closest element that encloses our current cursor
        position."""
        if self.tree.children:
            node, depth = self._closest_node(
                self.tree.children[0], 0, None, -1, self.misc.cursor())
            return node

    def _closest_node(self, tree, depth, closest_node, closest_depth, pos):
        """Finds the closest element that encloses our current cursor
        position."""
        row, col = pos
        startrow, startcol = tree.start[0], tree.start[1]
        endrow = tree.end[0]

        if tree.tag in self.empty_tags:
            endcol = tree.start[1] + len(tree.starttag_text)
        else:
            endcol = tree.end[1] + len(tree.tag) + 2

        # check if the current position is inside the element boundaries
        if startrow < row < endrow:
            cond = True
        elif startrow == row and endrow != row and startcol <= col:
            cond = True
        elif endrow == row and startrow != row and col <= endcol:
            cond = True
        elif startrow == row and endrow == row and startcol <= col <= endcol:
            cond = True
        else:
            cond = False

        # if cond is True the element encloses our position and we temporarily
        # assume that this is the closest element relative to our position
        if cond:
            closest_node = tree
            closest_depth = depth

        # check recursively for the closest element
        for c in tree.children:
            n, d, = self._closest_node(
                        c, depth + 1, closest_node, closest_depth, pos)

            if d > closest_depth:
                closest_node = n
                closest_depth = d

            if depth < closest_depth:
                # we have already found the closest node and we are going up
                # the tree structure (depth < closest_depth). There is no
                # need to continue the search
                return closest_node, closest_depth

        return closest_node, closest_depth

    def print_dom_tree(self, indent=2):
        """Print the parsed DOM tree."""

        def _print_tree(tree, depth, indent):
            """Internal function for printing the HTML tree."""
            print(" " * depth + tree.tag)
            for c in tree.children:
                _print_tree(c, depth + indent, indent)

        if self.tree.children:
            _print_tree(self.tree.children[0], 0, indent)

    def all_nodes(self):
        """Returns all DOM nodes as a generator."""

        def _flatten(tree):
            g = [tree]
            for c in tree.children:
                g = itertools.chain(g, _flatten(c))
            return g

        if self.tree.children:
            return _flatten(self.tree.children[0])
        else:
            return []

    def whats_wrong(self):
        """If something went wrong during the last parse,
        tell the user about it."""
        if self.last_known_error is not None:
            self.misc.echom("Error found at {pos}, type: {msg}".format(
                **self.last_known_error))
        else:
            self.misc.echom("All should be fine!")

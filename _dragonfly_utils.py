#!/usr/bin/env python
# (c) Copyright 2015 by James Stout
# Licensed under the LGPL, see <http://www.gnu.org/licenses/>

"""Various utility functions for working with dragonfly."""

import json
import os
import os.path
import tempfile

from dragonfly import (
    ActionBase,
    Key,
    MappingRule,
    Repetition,
    Sequence,
    Text,
)

#-------------------------------------------------------------------------------
# Utility functions and classes for manipulating grammars and their components.
# To make creating rules a bit easier, we define a few new types:
# Action map: Mapping from command spec (string) to action.
# Element map: Mapping from element name to either element or tuple of element
#              and default value. The preset element names will be overwritten
#              when used.
#
# The advantage to this separation is we can easily bind a single element to
# different names to be used in multiple rules, and we can easily create rules
# on the fly without defining a new class.

def combine_maps(*maps):
    """Merge the contents of multiple maps, giving precedence to later maps."""
    result = {}
    for map in maps:
        if map:
            result.update(map)
    return result


def text_map_to_action_map(text_map):
    """Converts string values in a map to text actions."""
    return dict((k, Text(v.replace("%", "%%")))
                for (k, v) in text_map.iteritems())


class JoinedRepetition(Repetition):
    """Like Repetition, except the results are joined with the given delimiter
    instead of returned as a list.
    """

    def __init__(self, delimiter, *args, **kwargs):
        Repetition.__init__(self, *args, **kwargs)
        self.delimiter = delimiter

    def value(self, node):
        return self.delimiter.join(Repetition.value(self, node))

class JoinedSequence(Sequence):
    """Like Sequence, except the results are joined with the given delimiter instead
    of returned as a list.
    """

    def __init__(self, delimiter, *args, **kwargs):
        Sequence.__init__(self, *args, **kwargs)
        self.delimiter = delimiter

    def value(self, node):
        return self.delimiter.join(str(v)
                                   for v in Sequence.value(self, node)
                                   if v)


class ElementWrapper(Sequence):
    """Identity function on element, useful for renaming."""

    def __init__(self, name, child):
        Sequence.__init__(self, (child, ), name)

    def value(self, node):
        return Sequence.value(self, node)[0]


def element_map_to_extras(element_map):
    """Converts an element map to a standard named element list that may be used in
    MappingRule.
    """
    return [ElementWrapper(name, element[0] if isinstance(element, tuple) else element)
            for (name, element) in element_map.items()]


def element_map_to_defaults(element_map):
    """Converts an element map to a map of element names to default values."""
    return dict([(name, element[1])
                 for (name, element) in element_map.items()
                 if isinstance(element, tuple)])


def create_rule(name, action_map, element_map, exported=False, context=None):
    """Creates a rule with the given name, binding the given element map to the
    action map.
    """
    return MappingRule(name,
                       action_map,
                       element_map_to_extras(element_map),
                       element_map_to_defaults(element_map),
                       exported,
                       context=context)


def combine_contexts(context1, context2):
    """Combine two contexts using "&", treating None as equivalent to a context that
    matches everything.
    """
    if not context1:
        return context2
    if not context2:
        return context1
    return context1 & context2
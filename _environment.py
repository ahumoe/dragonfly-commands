# (c) Copyright 2015 by James Stout
# (c) Copyright 2016 by Andreas Hagen Ulltveit-Moe
# Licensed under the LGPL, see <http://www.gnu.org/licenses/>

from _dragonfly_utils import (
    combine_contexts,
    combine_maps,
    create_rule,
)
from _repeat_rule_grammar import RepeatRule

from dragonfly import (
    RuleRef,
    Empty,
)

#-------------------------------------------------------------------------------
# Define top-level rules for different contexts. Note that Dragon only allows
# top-level rules to be context-specific, but we want control over sub-rules. To
# work around this limitation, we compile a mutually exclusive top-level rule
# for each context.

class Environment(object):
    """Environment where voice commands can be spoken. Combines grammar and context
    and adds hierarchy. When installed, will produce a top-level rule for each
    environment.
    """

    def __init__(self,
                 name,
                 parent=None,
                 context=None,
                 action_map=None,
                 terminal_action_map=None,
                 element_map=None):
        self.name = name
        self.children = []
        if parent:
            parent.add_child(self)
            self.context = combine_contexts(parent.context, context)
            self.action_map = combine_maps(parent.action_map, action_map)
            self.terminal_action_map = combine_maps(
                parent.terminal_action_map, terminal_action_map)
            self.element_map = combine_maps(parent.element_map, element_map)
        else:
            self.context = context
            self.action_map = action_map if action_map else {}
            self.terminal_action_map = terminal_action_map if terminal_action_map else {}
            self.element_map = element_map if element_map else {}

    def add_child(self, child):
        self.children.append(child)

    def install(self, grammar):
        exclusive_context = self.context
        for child in self.children:
            child.install(grammar)
            exclusive_context = combine_contexts(exclusive_context, ~child.context)
        if self.action_map:
            element = RuleRef(rule=create_rule(self.name + "KeystrokeRule",
                                                     self.action_map,
                                                     self.element_map))
        else:
            element = Empty()
        if self.terminal_action_map:
            terminal_element = RuleRef(
                rule=create_rule(self.name + "TerminalRule",
                                       self.terminal_action_map,
                                       self.element_map))
        else:
            terminal_element = Empty()
        grammar.add_rule(RepeatRule(self.name + "RepeatRule",
                                    element,
                                    terminal_element,
                                    exclusive_context))

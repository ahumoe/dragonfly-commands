# (c) Copyright 2015 by James Stout
# (c) Copyright 2016 by Andreas Hagen Ulltveit-Moe
# Licensed under the LGPL, see <http://www.gnu.org/licenses/>

from _dragonfly_utils import ElementWrapper
from _characters_and_numbers import character_rule
from _problematic_chars import release
from _window_switching import final_rule

from dragonfly import (
    Alternative,
    CompoundRule,
    Pause,
    Repetition,
    RuleRef,
)

# This is the rule that actually handles recognitions.
#  When a recognition occurs, its _process_recognition()
#  method will be called.  It receives information about the
#  recognition in the "extras" argument: the sequence of
#  actions and the number of times to repeat them.
class RepeatRule(CompoundRule):

    def __init__(self, name, command, terminal_command, context):
        # Here we define this rule's spoken-form and special elements. Note that
        # nested_repetitions is the only one that contains Repetitions, and it
        # is not itself repeated. This is for performance purposes.
        spec = ("[<sequence>] "
                "[<nested_repetitions>] "
                "[<terminal_command>] "
                "[<final_command>]")
        extras = [
            Repetition(command, min=1, max = 5, name="sequence"),
            Alternative([RuleRef(rule=character_rule)],
                        name="nested_repetitions"),
            ElementWrapper("terminal_command", terminal_command),
            RuleRef(rule=final_rule, name="final_command"),
        ]
        defaults = {
            "sequence": [],
            "nested_repetitions": None,
            "terminal_command": None,
            "final_command": None,
        }

        CompoundRule.__init__(self, name=name, spec=spec,
                              extras=extras, defaults=defaults, exported=True, context=context)

    # This method gets called when this rule is recognized.
    # Arguments:
    #  - node -- root node of the recognition parse tree.
    #  - extras -- dict of the "extras" special elements:
    #     . extras["sequence"] gives the sequence of actions.
    def _process_recognition(self, node, extras):
        sequence = extras["sequence"]   # A sequence of actions.
        nested_repetitions = extras["nested_repetitions"]
        terminal_command = extras["terminal_command"]
        final_command = extras["final_command"]
        for action in sequence:
            action.execute()
            Pause("5").execute()
        if nested_repetitions:
            nested_repetitions.execute()
        if terminal_command:
            terminal_command.execute()
        release.execute()
        if final_command:
            final_command.execute()

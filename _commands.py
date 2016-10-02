#
# This file is a command-module for Dragonfly.
# (c) Copyright 2008 by Christo Butcher
# (c) Copyright 2015 by James Stout
# (c) Copyright 2016 by Andreas Hagen Ulltveit-Moe
# Licensed under the LGPL, see <http://www.gnu.org/licenses/>
#

"""This contains all commands which may be spoken continuously or repeated.

This file is based on _repeat.py, found here:
https://github.com/wolfmanstout/dragonfly-commands/blob/master/_repeat.py
"""

try:
    import pkg_resources
    pkg_resources.require("dragonfly >= 0.6.5beta1.dev-r99")
except ImportError:
    pass

import Queue
import platform
import socket
import threading
import time
import webbrowser
import win32clipboard

from dragonfly import (
    ActionBase,
    Alternative,
    AppContext,
    CompoundRule,
    Config,
    DictList,
    DictListRef,
    Dictation,
    Empty,
    Function,
    Grammar,
    IntegerRef,
    Key,
    List,
    ListRef,
    Mimic,
    Mouse,
    Optional,
    Pause,
    Repeat,
    Repetition,
    RuleRef,
    RuleWrap,
    Text,
    get_engine,
)

import dragonfly.log
import _dragonfly_utils as utils
import _personal_info as info

from _problematic_chars import (
    release,
    lbrace,
    rbrace,
    lbracket,
    rbracket,
    hashk,
    backslash,
    tilde,
    pipe,
    caret,
)

from _format_text_actions import (
    TextAction,
    CamelAction,
    CapsAction,
    DashAction,
    UpperScoreAction,
    TwoCamelAction,
)

# Make sure dragonfly errors show up in NatLink messages.
dragonfly.log.setup_log()

# Load _commands.txt.
config = Config("commands")
namespace = config.load()

#-------------------------------------------------------------------------------
# Common maps and lists.
symbol_map = {
    "plus": " + ",
    "dub plus": "++",
    "minus": " - ",
    "come": ", ",
    "place": ": ",
    "fuel": ":",
    "equals": " = ",
    "dub equals": " == ",
    "bang it": " != ",
    "plus it": " += ",
    "greater than": " > ",
    "less than": " < ",
    "greater equals": " >= ",
    "less equals": " <= ",
    "fleck": ".",
    "leap": "(",
    "reap": ")",
    #"lake": "{"
    #"rake": "}",
    #"lobe":  "[",
    #"robe":  "]",
    "luke": "<",
    "dub luke": " << ",
    "ruke": ">",
    "quote": "\"",
    "dash": "-",
    "geek": ";",
    "bang": "!",
    "percent": "%",
    "star": "*",
    #"backslash": "\\",
    "slash": "/",
    #"tilde": "~", 
    "floor": "_",
    "sick quote": "'",
    #"dollar": "$",
    #"carrot": "^",
    "arrow": " ->" ,
    "fat arrow": " => ",
    "dub coal": "::",
    "amper": "&",
    "dub and": " && ",
    #"pipe": "|",
    #"dub pipe": " || ",
    #"hash": "#",
    #"at symbol": "@",
    "question": "?",
    "space": " ", 
}

numbers_map = {
    "zero": "0",
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "nine": "9",
    "point": ".",
    "minus": "-",
    "slash": "/",
    "coal": ":",
    "come": ", ",
}

short_letters_map = {
    "A": "a",
    "B": "b",
    "C": "c",
    "D": "d",
    "E": "e",
    "F": "f",
    "G": "g",
    "H": "h",
    "I": "i",
    "J": "j",
    "K": "k",
    "L": "l",
    "M": "m",
    "N": "n",
    "O": "o",
    "P": "p",
    "Q": "q",
    "R": "r",
    "S": "s",
    "T": "t",
    "U": "u",
    "V": "v",
    "W": "w",
    "X": "x",
    "Y": "y",
    "Z": "z",
}

letters_map = {
    "ace": "a",
    "bed": "b",
    "chair": "c",
    "dell": "d",
    "egg": "e",
    "fame": "f",
    "golf": "g",
    "heart": "h",
    "ice": "i",
    "joy": "j",
    "king": "k",
    "love": "l",
    "mars": "m",
    "neck": "n",
    "ork": "o",
    "pork": "p",
    "quest": "q",
    "rug": "r",
    "sea": "s",
    "tan": "t",
    "ush": "u",
    "van": "v",
    "wish": "w",
    "trex": "x",
    "yang": "y",
    "zulu": "z",
}

prefixes = [
    "num",
    "min",
]

suffixes = [
    "bytes",
]

char_map = dict((k, v.strip())
                for (k, v) in utils.combine_maps(letters_map, symbol_map).iteritems())

### Final commands that can be used once after everything else. These change the
### application context so it is important that nothing else gets run after
### them.

outlook_n = "6"
slack_n = "7"

# Ordered list of pinned taskbar items. Sublists refer to windows within a specific application.
windows = [
    "browse",
    "code",
    "storm",  
    "text",
    "source",
    "email", # 6
    "slack", # 7
    "paint",
    "explore",  
]

windows_prefix = "go"
windows_mapping = {}
for i, window in enumerate(windows):
    if isinstance(window, str):
        window = [window]
    for j, words in enumerate(window):
        windows_mapping[windows_prefix + " " + words] = Key("win:down, %d:%d/10, win:up" % (i + 1, j + 1))

# Work around security restrictions in Windows 8.
if platform.release() == "8":
    swap_action = Mimic("press", "alt", "tab")
else:
    swap_action = Key("alt:down, tab:%(n)d/25, alt:up")

final_action_map = utils.combine_maps(windows_mapping, {
    "swap [<n>]":   swap_action,
})
final_element_map = {
    "n": (IntegerRef(None, 1, 20), 1)
}
final_rule = utils.create_rule("FinalRule",
                               final_action_map,
                               final_element_map)

#-------------------------------------------------------------------------------
# Action maps to be used in rules.

# Key actions which may be used anywhere in any command.
global_key_action_map = {
    "punch [<n>]": Key("enter/5:%(n)d"),
    "tab [<n>]": Key("tab/5:%(n)d"),
}

class ToDir(ActionBase):

    def __init__(self, path, run_explorer=False):
        super(ToDir, self).__init__()
        select_bar = Key("c-l/15")
        open_run = Key("w-r/60")
        self.prefix = open_run if run_explorer else select_bar 
        self.clipboard = "explorer.exe " + path if run_explorer else path

    def _execute(self, data=None):
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        try:
            win32clipboard.SetClipboardData(win32clipboard.CF_UNICODETEXT, unicode(self.clipboard))
        finally:
            win32clipboard.CloseClipboard()
            action = self.prefix + Key("c-v/5, enter")
            action.execute() 


# Actions of commonly used text navigation and mousing commands. These can be
# used anywhere except after commands which include arbitrary dictation.

key_action_map = {

    # Navigation
    "up [<n>]":         Key("up/5:%(n)d"),
    "down [<n>]":       Key("down/5:%(n)d"),
    "left [<n>]":       Key("left/5:%(n)d"),
    "right [<n>]":      Key("right/5:%(n)d"),
   
    "lord [<n>]":       Key("c-left/5:%(n)d"),
    "sword [<n>]":      Key("c-right/5:%(n)d"),

    "west":             Key("home"),
    "east":             Key("end"),

    "page up [<n>]":        Key("pgup/5:%(n)d"),
    "page down [<n>]":      Key("pgdown/5:%(n)d"),
    "north":                Key("c-home"),
    "south":                Key("c-end"),

    # Deletion
    "crash [<n>]":      Key("backspace/5:%(n)d"), 
    "crack [<n>]":      Key("del/5:%(n)d"),
    "slay [<n>]":       release + Key("c-backspace/5:%(n)d"),
    "kill [<n>]":       release + Key("c-del/5:%(n)d"),
    
    # Copy/paste
    "copy":         release + Key("c-c") +  Mouse("left:up"),
    "paste":        release + Key("c-v"),
    "cut [<n>]":    release + Key("c-x/5:%(n)d"),
    
    # Selection
    "mark all":             release + Key("c-a"),
    "mark line":            release + Key("home/5, shift:down/5, end"),
    "mark west":            release + Key("shift:down, home"),
    "mark east":            release + Key("shift:down, end"),

    "mark right [<n>]":     release + Key("shift:down, c-right/5:%(n)d"),
    "mark left [<n>]":      release + Key("shift:down, c-left/5:%(n)d"),
    "mark up [<n>]":        release + Key("shift:down/5, up/5:%(n)d, home"), # cursor should be at end of line
    "mark down [<n>]":      release + Key("shift:down/5, down/5:%(n)d, end"), # cursor should be at start of line
    "mark it":              release + Key("c-right/5, shift:down, c-left"), 

    # Mouse
    "fish":         Mouse("left"),
    "fish right":   Mouse("right"), #TODO: dont work!
    "middle":       Mouse("middle"),
    "fish twice":   Mouse("left:2"),
    "drag":         Mouse("left:down"),
    "break":        Mouse("left:up"),

    # Windows
    "pop up":           Key("apps"),
    "do left":          Key("w-left"),
    "do right":         Key("w-right"),
    "do up":            Key("w-up"),
    "do down":          Key("w-down:2"),
    "go desk":          Key("w-d"),
    "control panel":    Key("win/15") + Text("control panel") + Key("space/15") + Key("enter"), 

    # Undo/redo
    "fail [<n>]":       Key("c-z/5:%(n)d"),
    "redo [<n>]":       Key("c-y/5:%(n)d"),

    # Filesystem
    "save":             Key("c-s"),
    "save as":          Key("cs-s"),
    "file rename":      Key("f2"), 
    "open box":         ToDir(info.DOWNLOAD, True), 

    # Misc
    "find":                 Key("c-f"),
    "escape|quit":          Key("escape"),
    "race":                 Key("end/5, enter"),
    "coke [<n>]":           Key("s-tab/5:%(n)d"),   
    "mouse run":            Key("csa-m"), 

    # Dragon - remapped in Dragon-options
    "act off":      Key("csa-d"), 
    "act sleep":    Key("csa-f"),
   
    # Symbols not working in the symbol_map, written as commands here
    "lake":             lbrace, # {
    "rake":             rbrace, # }
    "lobe":             lbracket, # [
    "robe":             rbracket, # ]
    "caret":            caret, # ^
    "rear back":        backslash,
    "pipe":             pipe, 
    "dollar":           Key("ca-4"),
    "hash":             Key("s-3"),
    "at symbol":        Key("ca-at"),
    "tilde":            tilde, # ~
}

# Actions for speaking out sequences of characters.
character_action_map = {
    "sign <numerals>": Text("%(numerals)s"),
    "print <letters>": Text("%(letters)s"),
    "shout <letters>": Function(lambda letters: Text(letters.upper()).execute()),
}

# Actions that can be used anywhere in any command.
global_action_map = utils.combine_maps(global_key_action_map,
                                       utils.text_map_to_action_map(symbol_map))

# Actions that can be used anywhere except after a command with arbitrary
# dictation.
command_action_map = utils.combine_maps(global_action_map, key_action_map)

# Here we prepare the action map of formatting functions from the config file.
# Retrieve text-formatting functions from this module's config file. Each of
# these functions must have a name that starts with "format_".
format_functions = {}
if namespace:
    for name, function in namespace.items():
        if name.startswith("format_") and callable(function):
            spoken_form = function.__doc__.strip()

            # We wrap generation of the Function action in a function so
            #  that its *function* variable will be local.  Otherwise it
            #  would change during the next iteration of the namespace loop.
            def wrap_function(function):
                def _function(dictation):
                    formatted_text = function(dictation)
                    Text(formatted_text).execute()
                return Function(_function)

            action = wrap_function(function)
            format_functions[spoken_form] = action

#-------------------------------------------------------------------------------
# Simple elements that may be referred to within a rule.

numbers_dict_list  = DictList("numbers_dict_list", numbers_map)
letters_dict_list = DictList("letters_dict_list", letters_map)
char_dict_list = DictList("char_dict_list", char_map)
# Lists which will be populated later via RPC.
context_word_list = List("context_word_list", [])
prefix_list = List("prefix_list", prefixes)
suffix_list = List("suffix_list", suffixes)

# Either arbitrary dictation or letters.
mixed_dictation = RuleWrap(None, utils.JoinedSequence(" ", [
    Optional(ListRef(None, prefix_list)),
    Alternative([
        Dictation(),
        DictListRef(None, letters_dict_list),
    ]),
    Optional(ListRef(None, suffix_list)),
]))

# A sequence of either short letters or long letters.
letters_element = RuleWrap(None, utils.JoinedRepetition(
    "", DictListRef(None, letters_dict_list), min=1, max=10))

# A sequence of numbers.
numbers_element = RuleWrap(None, utils.JoinedRepetition(
    "", DictListRef(None, numbers_dict_list), min=0, max=10))

# A sequence of characters.
chars_element = RuleWrap(None, utils.JoinedRepetition(
    "", DictListRef(None, char_dict_list), min=0, max=10))

# Simple element map corresponding to keystroke action maps from earlier.
keystroke_element_map = {
    "n": (IntegerRef(None, 1, 21), 1),
    "text": Dictation(),
    "char": DictListRef(None, char_dict_list),
    "custom_text": RuleWrap(None, Alternative([
        Dictation(),
        DictListRef(None, char_dict_list),
        ListRef(None, prefix_list),
        ListRef(None, suffix_list),
    ])),
}

#-------------------------------------------------------------------------------
# Rules which we will refer to within other rules.

# Rule for formatting mixed_dictation elements.
format_rule = utils.create_rule(
    "FormatRule",
    format_functions,
    {"dictation": mixed_dictation}
)

start_menu_rule = utils.create_rule(
    "StartMenuRule",
    {
        "program <text>": Key("win/40") + Text("%(text)s"),
    },
    {
        "text": Dictation()
    }
)

# Rule for printing single characters.
single_character_rule = utils.create_rule(
    "SingleCharacterRule",
    character_action_map,
    {
        "numerals": DictListRef(None, numbers_dict_list),
        "letters": DictListRef(None, letters_dict_list),
        "chars": DictListRef(None, char_dict_list),
    }
)

# Rule for spelling a word letter by letter and formatting it.
spell_format_rule = utils.create_rule(
    "SpellFormatRule",
    dict([("spell " + k, v)
          for (k, v) in format_functions.items()]),
    {"dictation": letters_element}
)

# Rule for printing a sequence of characters.
character_rule = utils.create_rule(
    "CharacterRule",
    character_action_map,
    {
        "numerals": numbers_element,
        "letters": letters_element,
        "chars": chars_element,
    }
)

#-------------------------------------------------------------------------------
# Elements that are composed of rules. Note that the value of these elements are
# actions which will have to be triggered manually.

# Element matching simple commands.
# For efficiency, this should not contain any repeating elements.
single_action = RuleRef(rule=utils.create_rule("CommandKeystrokeRule",
                                               command_action_map,
                                               keystroke_element_map))

# Element matching dictation and commands allowed at the end of an utterance.
# For efficiency, this should not contain any repeating elements. For accuracy,
# few custom commands should be included to avoid clashes with dictation
# elements.
dictation_element = RuleWrap(None, Alternative([
    RuleRef(rule=start_menu_rule),
    RuleRef(rule=format_rule),
    RuleRef(rule=utils.create_rule("DictationKeystrokeRule",
                                   global_action_map,
                                   keystroke_element_map)),
    RuleRef(rule=single_character_rule),
]))




#---------------------------------------------------------------------------
# Here we define the top-level rule which the user can say.

# This is the rule that actually handles recognitions.
#  When a recognition occurs, its _process_recognition()
#  method will be called.  It receives information about the
#  recognition in the "extras" argument: the sequence of
#  actions and the number of times to repeat them.
class RepeatRule(CompoundRule):

    def __init__(self, name, command, terminal_command, context):
        # Here we define this rule's spoken-form and special elements. Note that
        # nested_repetitions is the only one that contains Repetitions, and it
        # is not itself repeated. This is for performance purposes. We also
        # include a special escape command "terminal <dictation>" in case
        # recognition problems occur with repeated dictation commands.
        spec = ("[<sequence>] "
                "[<nested_repetitions>] "
                "([<dictation_sequence>] [terminal <dictation>] | <terminal_command>) "
                "[[[and] repeat [that]] <n> times] "
                "[<final_command>]")
        extras = [
            Repetition(command, min=1, max = 5, name="sequence"),
            Alternative([RuleRef(rule=character_rule), RuleRef(rule=spell_format_rule)],
                        name="nested_repetitions"),
            Repetition(dictation_element, min=1, max=5, name="dictation_sequence"),
            utils.ElementWrapper("dictation", dictation_element),
            utils.ElementWrapper("terminal_command", terminal_command),
            IntegerRef("n", 1, 100),  # Times to repeat the sequence.
            RuleRef(rule=final_rule, name="final_command"),
        ]
        defaults = {
            "n": 1,                   # Default repeat count.
            "sequence": [],
            "nested_repetitions": None,
            "dictation_sequence": [],
            "dictation": None,
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
    #     . extras["n"] gives the repeat count.
    def _process_recognition(self, node, extras):
        sequence = extras["sequence"]   # A sequence of actions.
        nested_repetitions = extras["nested_repetitions"]
        dictation_sequence = extras["dictation_sequence"]
        dictation = extras["dictation"]
        terminal_command = extras["terminal_command"]
        final_command = extras["final_command"]
        count = extras["n"]             # An integer repeat count.
        for i in range(count):
            for action in sequence:
                action.execute()
                Pause("5").execute()
            if nested_repetitions:
                nested_repetitions.execute()
            for action in dictation_sequence:
                action.execute()
                Pause("5").execute()
            if dictation:
                dictation.execute()
            if terminal_command:
                terminal_command.execute()
        release.execute()
        if final_command:
            final_command.execute()


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
            self.context = utils.combine_contexts(parent.context, context)
            self.action_map = utils.combine_maps(parent.action_map, action_map)
            self.terminal_action_map = utils.combine_maps(
                parent.terminal_action_map, terminal_action_map)
            self.element_map = utils.combine_maps(parent.element_map, element_map)
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
            exclusive_context = utils.combine_contexts(exclusive_context, ~child.context)
        if self.action_map:
            element = RuleRef(rule=utils.create_rule(self.name + "KeystrokeRule",
                                                     self.action_map,
                                                     self.element_map))
        else:
            element = Empty()
        if self.terminal_action_map:
            terminal_element = RuleRef(
                rule=utils.create_rule(self.name + "TerminalRule",
                                       self.terminal_action_map,
                                       self.element_map))
        else:
            terminal_element = Empty()
        grammar.add_rule(RepeatRule(self.name + "RepeatRule",
                                    element,
                                    terminal_element,
                                    exclusive_context))


### Global

global_environment = Environment(name="Global",
                                 action_map=command_action_map,
                                 element_map=keystroke_element_map)

### Language action maps

programming_action_map = {
   
    # Macros
    "call out":     Key("end/5, lparen/5, rparen/5, semicolon/5, enter"),
    "last":         Key("end/5, semicolon/5, enter"), 
    "hit":          Key("end/5, comma/5, enter"),  

    "if":           Text("if ("),
    "box":          Text("var"), 
    "scope":        Key("end/5, space/5") + lbrace + Key("enter"),

}
 
programming_terminal_action_map = {
    
    # Common/general code
    "box <text1>":          CamelAction(Text("var ")), 
    "buff <text1>":         CamelAction(Text(" = ")),
    "if <text1>":           CamelAction(Text("if (")),
    "return <text1>":       CamelAction(Text("return ")), 
    "fleck <text1>":        CamelAction(Text(".")), 

    "hats <text1>":         CapsAction(Text(" = ")), 
    "new <text1>":          CapsAction(Text("new ")), 
    "now <text1>":          CapsAction(Text(" = new ")),  
    "grain <text1>":        CapsAction(Text(".")), 

    "add <text1>":          CamelAction(Text(" + ")), 
    "sub <text1>":          CamelAction(Text(" - ")), 
    "and <text1>":          CamelAction(Text(" && ")), 
    "or <text1>":           CamelAction(Text(" ") + pipe + pipe + Text(" ")),
    "like it <text1>":      CamelAction(Text(" == ")), 
    "not <text1>":          CamelAction(Text(" != ")),
    "less <text1>":         CamelAction(Text(" < ")), 
    "big <text1>":          CamelAction(Text(" > ")), 
    "lobe <text1>":         CamelAction(lbracket), # [..]
    "floor <text1>":        CamelAction(Text("_")), 
    "leap <text1>":         CamelAction(Text("(")),
    "quote <text1>":        TextAction(Text("\"")),

    # Marked words
    "true":         Text("true"),
    "false":        Text("false"),
    "else":         Text(" else ") + lbrace + Key("enter/5"), 

}

web_container_map = {
    "ace": "a",
    "dell": "div",
    "fame": "form",
    "ice": "input",
    "love": "li",
    "pork": "p",
    "sea": "span",
    "tan": "table",
    "ush": "ul",
}

web_container_map_dict_list = DictList("web_container_map_dict_list", web_container_map)

css_words_map = {
    "bed": "border",
    "chair": "color",
    "dell": "display",
    "fame": "font",
    "heart": "height",
    "mars": "margin",
    "pork": "padding",
    "wish": "width",
}

css_words_map_dict_list = DictList("css_words_map_dict_list", css_words_map)

web_action_map = {
   
    # HTML/CSS macros
    "jog":          Key("end/15, rangle/5, enter/5"),
    "pics":         Text("px;"),
    "path":         Text("href=") + Key("dquote"),

    "can <web_container>":        Text("%(web_container)s"), 
    "ring <web_container>":       Text("</%(web_container)s>"), 
    "sheet <css_word>":           Text("%(css_word)s"),
}


web_terminal_action_map = {

    # CSS
    "spot <text1>":         DashAction(Text(".")), 
    "size <num_seq>":       Text(": %(num_seq)s"), 
    "head <num_seq>":       Text("<h%(num_seq)s>"), 
}

js_action_map = {
    
    # JavaScript
    "funk":         Text("function () ") + lbrace + Key("enter"), 
    "third is":     Text(" === "),
    "this":         Text("this"), 
    "backfire":     Text("callback"), 
    "log":          Text("console.log("),

    "room":         lbrace + Key("enter"),

}

js_terminal_action_map = {

    # JavaScript
    "place <text1>":        CamelAction(Text(": ")),
    "no <text1>":           CamelAction(Text(" !== ")),
    "loop <text1>":         CamelAction(Text("for (var i = 0; i < "), Text("; i++) ")) + Key("left/5:7"),
    "math <text1>":         CamelAction(Text("function (")),  
    "funk <text1>":         CamelAction(Text("function ")), 
    "else if <text1>":      CamelAction(Text("else if (")), 

    "pack <text1>":         CapsAction(Text("var ")),
}

react_action_map = {
    
    # Frequently used words
    "export":       Text("export "), 
    "state":        Text("state"),
    "dispatch":     Text("dispatch"),
    "action":       Text("action"),
    "default":      Text("default "), 
    "const":        Text("const "),
    "props":        Text("this.props"), 
    "const":        Text("const "),
    "return":       Text("return "), 

    "spring":        Key("end/5, enter"), 

    # Writing HTML
    "frame":        Key("end") + Text("/>"), 
    
    # Finish element,  ex. </ul>
    "edge":         Key("end") + Text("</") + Key("c-left/5:3, enter"),
    
    "land":         Text(" => ") + lbrace + rbrace + Key("left/5, enter"),
    "trait":        Text("=") + lbrace, 

    "action switch":    Text("switch (action.type) ") + lbrace + Key("enter"), 
    "default switch":   Text("default:") + Key("enter") + Text("return state;"),
   
    "name":         Text("className='"), 

    # New component
    "class now":    Text(" = React.createClass(") + lbrace + Key("enter"), 
    "show funk":    Text("render: function()") + lbrace + Key("enter"),

}

react_terminal_action_map = {

    # Writing HTML
    "trunk <text1>":        CamelAction(Text("<div className='"), Text("'>") + Key("left/5:2")),
    "name <text1>":         CamelAction(Text("className='")),
    "base <text1>":         CapsAction(Text("<"), Text("/>")) + Key("left/5:2"), 
    "angle <text1>":        CapsAction(Text("<")),

    # Frequently used words
    "const <text1>":        CapsAction(Text("const ")),
    "dispatch <text1>":     CamelAction(Text("dispatch(")),
    "case <text1>":         UpperScoreAction(Text("case ")),

    "trait <text1>":        CamelAction(Text("=") + lbrace),
    "lake <text1>":         CamelAction(lbrace),
    "cite <text1>":         CamelAction(Text("('")), 
    "quote <text1>":        CamelAction(Text("'")),

}


c_sharp_action_map = {
    
    # C# marked words
    "pink":         Text("public "),
    "private":      Text("private "),
    "class":        Text("class "),
    "static":       Text("static "), 
    "shy":          Text("void "),
    "dead":         Text("null"),

    # C# types
    "I":            Text("int "),
    "bin":          Text("bool "),
    "string":       Text("string "),
    
    # C# macros
    "prop":         Key("space/5") + lbrace + Text(" get; set;") + Key("end/15, enter"),
    "not":          Text(" != "),
    "number":       Text("IEnumerable"), 
    "scope":        Key("end/5, enter/5") + lbrace + Key("enter"),

}

c_sharp_terminal_action_map = {
    
    # C# 
    "string <text1>":       CamelAction(Text("string ")),
    "bin <text1>":          CamelAction(Text("bool ")),
    "type <text1>":         CapsAction(suffix = Text(" ")), 
    "class <text1>":        CapsAction(Text("class ")), 
    "angle <text1>":        CapsAction(Key("langle/15")), 
    "number <text1>":       CapsAction(Text("IEnumerable<")),

    "land <text1>":                 CamelAction(suffix = Text(" => ")) + CamelAction(), 
    "loop <text1> in <text2>":      TwoCamelAction(Text("foreach (var "), Text(" in ")),
}

### Chrome

class RepeatAction(ActionBase): 
   
    def __init__(self, action):
        super(RepeatAction, self).__init__()
        self.action = action

    def _execute(self, data=None):
        repeat_action = Key("")
        for x in range(data["n"]):
            repeat_action += self.action
        repeat_action.execute()

letters_map_dict_list  = DictList("letters_map_dict_list", letters_map)

def open_website(url, delay=0):
    return Key("c-t/15") + Text(url) + Key("enter/" + str(delay))

chrome_action_map = {
    # https://support.google.com/chrome/answer/157179?hl=en

    # Tab and window shortcuts
    "now":              Key("c-t"),
    "spy":              Key("cs-n"),
    "new window":       Key("c-n"),
    "close [<n>]":      Key("c-w/5:%(n)d"),
    "live [<n>]":       Key("cs-t/5:%(n)d"),

    "back [<n>]":       Key("a-left/15:%(n)d"),
    "forward [<n>]":    Key("a-right/15:%(n)d"),
    "fresh":            Key("c-r"),
    
    "clone":            Key("as-d"), # mappped with "Duplicate Tab Shortcut Key" extension
    "next [<n>]":       Key("c-tab:%(n)d"),
    "pro [<n>]":        Key("cs-tab:%(n)d"),
    "to <n>":           Key("c-%(n)d"),
    "last":             Key("c-9"),
    
    # Google Chrome feature shortcuts
    "menu":             Key("a-f"),
    "full screen":      Key("f11"),
    "history":          Key("c-h"),    

    # Address bar shortcuts
    "bar":      Key("c-l"),
    
    # Webpage shortcuts
    "bookmark":         Key("c-d"),
    "pro match":        Key("cs-g"),
    "zoom":             Key("c-plus"),
    "zoom out":         Key("c-minus"),

    # Websites
    "page gmail":     open_website(info.GMAIL),
    "page code":      open_website(info.GITHUB),

    # Info
    "phone":            Text(info.PHONE),
    "number":           Text(info.NUMBER),
    "user":             Text(info.USER),
    "name":             Text(info.NAME),
    "first name":       Text(info.FIRST_NAME),
    "last name":        Text(info.LAST_NAME),

    "light":            Key("f"), # activate Vimium

    # Development
    "scan":                 Key("cs-c"),
    "pics":                 Text("px"), 
    "shift rise":           Key("s-up"), 
    "compute":              Mouse("[1460, 147], left"), # compute button
    "style":                Mouse("[1416, 215], left"), # element.style
    "read":                 Mouse("[1230, 428], left"), # DOM area
    "step [<n>]":           RepeatAction(Key("tab/5:2")),
    "walk [<n>]":           RepeatAction(Key("s-tab/5:2")),
    "sheet <css_word>":     Text("%(css_word)s"),

}

chrome_terminal_action_map = {
    "search <text>":    Key("c-t/15") + Text("%(text)s"),
    "find <text>":      Key("c-f/5") + Text("%(text)s"),
    "<letters>":        Text("%(letters)s"), # used with Vimium
}
 
chrome_element_map = {
    "n": (IntegerRef(None, 0, 10), 1),
    "letters": utils.JoinedRepetition(
          "", DictListRef(None, letters_map_dict_list), min=0, max=4),
    "css_word": DictListRef(None, css_words_map_dict_list),
}

chrome_environment = Environment(name="Chrome",
                                 parent=global_environment,
                                 context=AppContext(title=" - Google Chrome"),
                                 action_map=chrome_action_map,
                                 terminal_action_map=chrome_terminal_action_map,
                                 element_map=chrome_element_map)

### Visual Studio and WebStorm

class FindAction(CamelAction): 
   
    def __init__(self):
        super(FindAction, self).__init__(prefix=Key("c-f/15"))


studio_editor_action_map = {

    # VS tabs 
    "next [<n>]":       Key("c-tab/5:%(n)d"), # Window.NextTab remapped with Productivity Power Tools 
    "pro [<n>]":       Key("cs-tab/5:%(n)d"), # Window.PreviousTab remapped with Productivity Power Tools
    "close [<n>]":      Key("c-f4/5:%(n)d"), 

    # VS misc
    "cut [<n>]":            Key("c-x/15:%(n)d"),
    "drop [<n>]":           Key("cs-l/15:%(n)d"), 
    "line [<num_seq>]":     Key("c-g/15") + Text("%(num_seq)s") + Key("enter"),
    "back [<n>]":           Key("c-hyphen/15:%(n)d"),
    "forward [<n>]":        Key("cs-hyphen/15:%(n)d"),
    "search":               Key("cs-f/5"),
    "open project":         Key("cs-o"), 
    "packages":             Key("csa-n"), # mapped to Project.ManageNuGetPackages
    "options":              Key("csa-o"), # mapped to Tools.Options
    "show type":            Key("ctrl:down, k, i"), 
    "existing item":        Key("sa-a"),  
    "vertical":             Key("csa-v"), # mapped to Window.NewVerticalTabGroup
    
    # Build/run
    "build":            Key("cs-b"),
    "build again":      Key("cs-b, r"), # mapped to Build.RebuildSolution
    "clean it":         Key("cs-b, c"), # mapped to Build.CleanSolution
    "lunch [<n>]":      Key("f5/15:%(n)d"), # launch/continue application
    "restart":          Key("cs-f5"), 

    # Debuging
    "breakpoint":       Key("f9"), 
    "break it":         Mouse("left/5") + Key("f9"), 
    "germ it [<n>]":    Key("f10/15:%(n)d"), # step over
    "step into":        Key("f11"),
    "germ end":         Key("s-f5"),

}

studio_editor_terminal_action_map = {

    # Find/Search
    "search <text1>":       CamelAction(Key("cs-f/30")), # search solution
    "find <text1>":         FindAction(), # find in file
    "fly <text1>":          CamelAction(Key("cs-t/5")),  # search type/symbol/file name
    "file <letters>":       Key("cs-t/5") + Text("%(letters)s"), # search file name
    "symbol <letters>":     Key("sa-t/5") + Text("%(letters)s"), # search symbol   

    "supply class <text1>":    CapsAction(Key("ca-a, c/60, left/15, del/5:6")), # mapped to Project.AddClass

}

resharper_action_map = {
    # Visual Studio scheme:
    # https://www.jetbrains.com/help/resharper/2016.1/Reference__Keyboard_Shortcuts.html

    # Move code
    "code up [<n>]":        Key("csa-up/5:%(n)d"),
    "code down [<n>]":      Key("csa-down/5:%(n)d"),
    "art left [<n>]":       Key("csa-left/5:%(n)d"),
    "art right [<n>]":      Key("csa-right/5:%(n)d"),

    # Mark
    "light [<n>]":          Key("ca-right/5:%(n)d"),
    "shrink [<n>]":         Key("ca-left/5:%(n)d"),

    # Comment
    "cross [<n>]":          Key("ca-6/10:%(n)d") + Mouse("left:up"), # remapped LineComment
    "cross block":          Key("cs-6"), # remapped BlockComment

    # Snippets
    "surround":             Key("c-e, u"),
    "surround if":          Key("c-e, u/15, 1"),
    "surround if else":     Key("c-e, u/15, e"),
    "surround for":         Key("c-e, u/15, 3"),
    "surround leap":        Key("c-e, u/15, d"),

    "import it":            Key("a-enter"), 
    "make code":            Key("a-insert"), 
    "construct":            Key("a-insert/15, enter"), 

    # Bookmarks
    "set mark <n>":     Key("cs-%(n)d"),
    "bookmark <n>":     Key("c-%(n)d"),

    # Navigate to
    "changed [<n>]":    Key("cs-backspace/5:%(n)d"), # go to last edited location
    "recent":           Key("c-comma"), # show recent files
    "switch":           Key("c-comma/5, enter"),
    "tread":            Key("c-f12"),
    "move declare":     Key("f12"),
    "usage":            Key("sa-f12"),

    # Refactor
    "rename":           Key("c-r, r"),
    "to method":        Key("c-r, m"),
    "to box":           Key("c-r, v"),
    "cleanup":          Key("c-e, c"), 

    # Documentation
    "param":            Key("cs-space"),
    "quick doc":        Key("cs-f1"),

     # Misc
    "complete":         Key("c-space"),
    "clone":            Key("c-d"),
}

web_storm_editor_action_map = {
    
    # Tabs
    "next [<n>]":           Key("a-right/5:%(n)d"),
    "pro [<n>]":            Key("a-left/5:%(n)d"),
    "close [<n>]":          Key("c-f4/5:%(n)d"), 

    # Navigation
    "line [<num_seq>]":     Key("c-g/15") + Text("%(num_seq)s") + Key("enter"),
    "back [<n>]":           Key("ca-left/15:%(n)d"),
    "forward [<n>]":        Key("ca-right/15:%(n)d"),

    # Editing
    "drop [<n>]":           Key("c-y/15:%(n)d"), 

    # Misc
    "settings":             Key("ca-s"),
    "search":               Key("cs-f/5"),
    "open project":         Key("cs-o"), # mapped to Open
    "open recent":          Key("csa-o"), # mapped to Open recent
    "panel <n>":            Key("a-%(n)d"), 

    # Resharper type commands

    # Move code
    "code up [<n>]":        Key("cs-up/5:%(n)d"),
    "code down [<n>]":      Key("cs-down/5:%(n)d"),

    # Mark
    "light [<n>]":          Key("c-w/5:%(n)d"),
    "shrink [<n>]":         Key("cs-w/5:%(n)d"),

    # Comment
    "cross [<n>]":          Key("ca-6/10:%(n)d") + Mouse("left:up"), # remapped
    "cross block":          Key("csa-6") + Mouse("left:up"), # remapped

    # Snippets
    "surround":             Key("ca-t"),
    "surround if":          Key("ca-t/15, 1"),

    "import it":            Key("a-enter"), 
    "make code":            Key("a-insert"), 

    # Bookmarks
    "set mark <n>":     Key("cs-%(n)d"),
    "bookmark <n>":     Key("c-%(n)d"),

    # Navigate to
    "changed [<n>]":    Key("cs-backspace/5:%(n)d"), # go to last edited location
    "recent":           Key("c-e"), # show recent files
    "tread":            Key("ca-b"),
    "move declare":     Key("c-b"),
    "usage":            Key("a-f7"),
    "to type":          Key("cs-b"),
    "fly":              Key("shift:down/5, shift:up/5, shift:down/5, shift:up/5"), 

    # Refactor
    "rename":           Key("s-f6"),
    "to method":        Key("ca-m"),
    "to box":           Key("ca-v"),

    # Documentation
    "param":            Key("c-p"),
    "quick doc":        Key("c-q"),

     # Misc
    "complete":         Key("c-space"),
    "clone":            Key("c-d"), 
}

web_storm_terminal_action_map = {
   
    # Find/Search
    "search <text1>":       CamelAction(Key("cs-f/30")), # search solution
    "fly <text1>":          CamelAction(Key("shift:down/5, shift:up/5, shift:down/5, shift:up/5")),  # search everywhere
    "symbol <letters>":     Key("csa-n/5") + Text("%(letters)s"), # search symbol   
    "class <letters>":      Key("c-n/5") + Text("%(letters)s"), # search symbol   
}

# Merge the contents of multiple maps, giving precedence to later maps

front_end_action_map = utils.combine_maps(programming_action_map, 
                                            web_action_map,
                                            js_action_map)

                                            
front_end_terminal_action_map = utils.combine_maps(programming_terminal_action_map, 
                                                    web_terminal_action_map,  
                                                    js_terminal_action_map)

studio_action_map = utils.combine_maps(programming_action_map, 
                                        c_sharp_action_map,
                                        studio_editor_action_map, 
                                        resharper_action_map)

studio_terminal_action_map = utils.combine_maps(programming_terminal_action_map,
                                                c_sharp_terminal_action_map, 
                                                studio_editor_terminal_action_map)

web_storm_action_map = utils.combine_maps(front_end_action_map, 
                                            react_action_map, 
                                            web_storm_editor_action_map)

web_storm_terminal_action_map = utils.combine_maps(front_end_terminal_action_map,
                                                    react_terminal_action_map, 
                                                    web_storm_terminal_action_map)

line_char_map = {
    "zero": "0",
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "nine": "9",
}

line_char_dict_list  = DictList("line_char_dict_list", line_char_map)



studio_element_map = {
    "n": (IntegerRef(None, 0, 100), 1),
    "num_seq": utils.JoinedRepetition(
        "", DictListRef(None, line_char_dict_list), min=0, max=6), 
    "letters": utils.JoinedRepetition(
        "", DictListRef(None, letters_map_dict_list), min=0, max=4), 
    "text1": RuleWrap(None, Alternative([
        Dictation(),
        DictListRef(None, char_dict_list),
    ])), 
    "text2": RuleWrap(None, Alternative([
        Dictation(),
        DictListRef(None, char_dict_list),
    ])), 
}

visual_studio_environment = Environment(name="Visual_studio",
                                 parent=global_environment,
                                 context=AppContext(title=" - Microsoft Visual Studio"),
                                 action_map=studio_action_map,
                                 terminal_action_map=studio_terminal_action_map,
                                 element_map=studio_element_map)

web_storm_element_map = {
    "n": (IntegerRef(None, 0, 100), 1),   
    "web_container": DictListRef(None, web_container_map_dict_list),
    "css_word": DictListRef(None, css_words_map_dict_list),
    "num_seq": utils.JoinedRepetition(
        "", DictListRef(None, line_char_dict_list), min=0, max=6), 
    "letters": utils.JoinedRepetition(
        "", DictListRef(None, letters_map_dict_list), min=0, max=4),
    "text1": RuleWrap(None, Alternative([
        Dictation(),
        DictListRef(None, char_dict_list),
    ])), 
}

web_storm_environment = Environment(name="Web_storm",
                                 parent=global_environment,
                                 context=AppContext(executable="WebStorm"),
                                 action_map=web_storm_action_map,
                                 terminal_action_map=web_storm_terminal_action_map,
                                 element_map=web_storm_element_map)

### SourceTree
### Version 1.8.2.11

class StageDiscardHunkAction(ActionBase): 
   
    def __init__(self, operation="stage"):
        super(StageDiscardHunkAction, self).__init__()
        self.operation = operation
        self.file_area  = Mouse("[1240, 185]")

    def _execute(self, data=None):
        extra_tab = 1 if self.operation == "discard" else 0
        key_string =  "tab/5:" + str(data["n1"] * 4 + extra_tab)
        action = self.file_area + Key(key_string)
        action.execute()
   
class ClickFileAction(ActionBase): 
   
    def __init__(self, mouse_x = 320, mouse_y = 590):
        super(ClickFileAction, self).__init__()
        self.mouse_x = mouse_x
        self.mouse_y = mouse_y

    def _execute(self, data=None):
        mouse_x =  str(self.mouse_x + (data["n2"] - 1) * 2)
        mouse_y =  str(self.mouse_y + (data["n2"] - 1) * 30)
        action = Mouse("[" + mouse_x + ", " + mouse_y + "]")
        action.execute()

class PickFileAction(ClickFileAction): 
   
    def __init__(self):
        super(PickFileAction, self).__init__(322, 180)   

terminal = Mouse("[720, 72]/200")

source_tree_action_map = {
    # http://greena13.github.io/blog/2015/02/01/sourcetree-keyboard-shortcuts/

    # Tabs
    "status|one":       Key("c-1"),
    "log|two":          Key("c-2"), 
    "search|three":     Key("c-3"), 

    # Committing
    "stage <n1>":       StageDiscardHunkAction("stage"),
    "discard <n1>":     StageDiscardHunkAction("discard"),
    "file [<n2>]":      ClickFileAction(), 
    "pick [<n2>]":      PickFileAction(), # Click file in staging area
    "stage file":       Key("space/30") + Mouse("[320, 590]/15, [323, 587]"), 
    "message":          Mouse("[1849, 966]"), # Click message field/cancel btn
    "commit":           Key("c-enter"),
    "read":             Mouse("[1240, 185]"), # Click file area (enable scrolling)
    
    # Terminal        
    "soft reset":       terminal + Text("git reset --soft HEAD") + tilde,
    "new base":         terminal + Text("git rebase -i HEAD"),

    # Other
    "pull":             release + Key("ctrl:down, shift:down, l"),
    "push":             release + Key("ctrl:down, shift:down, p"),
    "stash":            release + Key("ctrl:down, shift:down, s"),
    "open":             Key("c-o"), 
}

file_extension = Text(".cs")
source_tree_terminal_map = {
    "patch <text1>":         CapsAction(terminal + Text("git add --patch *"), file_extension),
}

source_tree_element_map = {
    "n1": IntegerRef(None, 0, 10), 
    "n2": (IntegerRef(None, 0, 10), 1), 
    "text1": RuleWrap(None, Alternative([
        Dictation(),
        DictListRef(None, char_dict_list),
    ])),
}


source_tree = Environment(name="Source_tree",
                                 parent=global_environment,
                                 context=AppContext(executable="SourceTree"),
                                 action_map=source_tree_action_map,
                                 terminal_action_map=source_tree_terminal_map,
                                 element_map=source_tree_element_map)


### Outlook

class ClickMailAction(ActionBase): 
   
    def __init__(self):
        super(ClickMailAction, self).__init__()
        self.start_y = 252
        self.start_x = 450

    def _execute(self, data=None):
        mouse_y =  str(self.start_y + (data["n"] - 1) * 64)
        mouse_x =  str(self.start_x + (data["n"] - 1) * 2)
        action = Mouse("[" + mouse_x + ", " + mouse_y + "]")
        action.execute()

outlook_action_map  = {
    # https://support.office.com/en-us/article/Keyboard-shortcuts-for-Outlook-3cdeb221-7ae5-4c1d-8c1d-9e63216c1efd
    
    # Boxes
    "box":          Mouse("[135, 235]"), # Inbox
    "unread":       Mouse("[137, 270]"), # Unread Mail
    "sent":         Mouse("[139, 300]"), # Sent Items

    "<n>":          ClickMailAction(),

    "no":           Key("c-u"), # Mark unread
    "now":          Key("cs-m/30, tab/5:3"),
    "item":         Key("c-n"), # new E-mail/appointment
    "search":       Key("c-e"),

    # Tabs
    "mail":         Key("c-1"),
    "time":         Key("c-2"),
    "people":       Key("c-3"),
}

outlook_terminal_map = {
    "search <text1>":       TextAction(Key("c-e/15")),
}

outlook_element_map = {
    "n": IntegerRef(None, 0, 10), 
    "text1": RuleWrap(None, Alternative([
        Dictation(),
        DictListRef(None, char_dict_list),
    ])),
}


outlook = Environment(name="Outlook",
                                 parent=global_environment,
                                 context=AppContext(title="- Outlook"),
                                 action_map=outlook_action_map,
                                 terminal_action_map=outlook_terminal_map,
                                 element_map=outlook_element_map)

### Sublime Text

sublime_action_map  = {
    
    # Tabs
    "close [<n>]":      Key("c-w/5:%(n)d"),
    "next [<n>]":       Key("c-pgdown/5:%(n)d"), 
    "pro [<n>]":        Key("c-pgup/15:%(n)d"),
    "vertical":         Key("as-2"), 
    "one column":       Key("as-1"), 

    # Misc
    "hash":             hashk + Key("space"),
    "now":              Key("c-n"), 
    "replace":          Key("c-h"),
    "cross [<n>]":      RepeatAction(Key("home/5, s-3/5, space/5, down/5, home/5")),

   # Dragonfly
   "text":              Text("Text(\""),   
   "key":               Text("Key(\""),   
}

sublime_terminal_map = {
    "find <text1>":    FindAction(),

    # Dragonfly
    "text <text1>":    CamelAction(Text("Text(\"")),   
    "key <text1>":     CamelAction(Text("Key(\"")), 
}

sublime_element_map = {
   "text1": RuleWrap(None, Alternative([
        Dictation(),
        DictListRef(None, char_dict_list),
    ])),
}

sublime_action_map = utils.combine_maps(sublime_action_map, 
                                        programming_action_map)

sublime_terminal_map = utils.combine_maps(sublime_terminal_map, 
                                            programming_terminal_action_map)

sublime = Environment(name="Sublime_Text",
                                 parent=global_environment,
                                 context=AppContext(title="- Sublime Text"),
                                 action_map=sublime_action_map,
                                 terminal_action_map=sublime_terminal_map,
                                 element_map=sublime_element_map)

### Slack

slack_action_map  = {
    # https://get.slack.help/hc/en-us/articles/201374536-Slack-keyboard-shortcuts

    # Navigation
    "pro [<n>]":         Key("a-up/5:%(n)d"), # Previous item
    "next [<n>]":         Key("a-down/5:%(n)d"), # Next item

    "read [<n>]":         Key("as-down/5:%(n)d"), # Next unread message

    "back [<n>]":         Key("a-left/5:%(n)d"), # Previous item in history
    "forward [<n>]":      Key("a-right/5:%(n)d"), # Next item in history

    # Channels
    "firm|one":         Key("c-1"),
    "intern|two":       Key("c-2"),

}

slack_terminal_map = {
    "now <letters>":        Key("cs-t/15") + Text("%(letters)s"), 
}

slack_element_map = {
    "letters": utils.JoinedRepetition(
        "", DictListRef(None, letters_map_dict_list), min=0, max=4), 
}


slack = Environment(name="Slack",
                     parent=global_environment,
                     context=AppContext(executable="Slack"),
                     action_map=slack_action_map,
                     terminal_action_map=slack_terminal_map,
                     element_map=slack_element_map)


### Windows Explorer

explorer_action_map  = {
   
    # Navigation
    "back [<n>]":         Key("a-left/5:%(n)d"), # Previous folder in history
    "forward [<n>]":      Key("a-right/5:%(n)d"), # Next folder in history

    "pro [<n>]":         Key("a-up/5:%(n)d"), # Up one level
    "recent":            Key("f4"),

    # Directories
    "drive":        ToDir(info.C_DRIVE), 
    "box":          ToDir(info.DOWNLOAD), 
    "documents":    ToDir(info.DOCUMENTS), 

}

explorer_terminal_map = {
    "search <text1>":         CapsAction(Key("c-e")),

}

explorer_element_map = {
    "text1": RuleWrap(None, Alternative([
        Dictation(),
        DictListRef(None, char_dict_list),
    ])),
}


explorer = Environment(name="Windows_Explorer",
                     parent=global_environment,
                     context=AppContext(executable="explorer"),
                     action_map=explorer_action_map,
                     terminal_action_map=explorer_terminal_map,
                     element_map=explorer_element_map)

#-------------------------------------------------------------------------------
# Populate and load the grammar.

grammar = Grammar("repeat")   # Create this module's grammar.
global_environment.install(grammar)
grammar.load()



#-------------------------------------------------------------------------------
# Unload function which will be called by NatLink.
def unload():
    global grammar
    if grammar:
        grammar.unload()
        grammar = None
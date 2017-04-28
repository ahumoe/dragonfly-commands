import _dragonfly_utils as utils

from dragonfly import (
    DictList,
    DictListRef,
    Function,
    RuleWrap,
    Text,
)

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

# Actions for speaking out sequences of characters.
character_action_map = {
    "sign <numerals>": Text("%(numerals)s"),
    "print <letters>": Text("%(letters)s"),
    "shout <letters>": Function(lambda letters: Text(letters.upper()).execute()),
}

char_map = dict((k, v.strip())
                for (k, v) in utils.combine_maps(letters_map).iteritems())

# Simple elements that may be referred to within a rule.
numbers_dict_list  = DictList("numbers_dict_list", numbers_map)
letters_dict_list = DictList("letters_dict_list", letters_map)
char_dict_list = DictList("char_dict_list", char_map)
letters_map_dict_list = DictList("letters_map_dict_list", letters_map)

# A sequence of either short letters or long letters.
letters_element = RuleWrap(None, utils.JoinedRepetition(
    "", DictListRef(None, letters_dict_list), min=1, max=10))

# A sequence of numbers.
numbers_element = RuleWrap(None, utils.JoinedRepetition(
    "", DictListRef(None, numbers_dict_list), min=0, max=10))

# A sequence of characters.
chars_element = RuleWrap(None, utils.JoinedRepetition(
    "", DictListRef(None, char_dict_list), min=0, max=10))

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

# (c) Copyright 2015 by James Stout
# (c) Copyright 2016 by Andreas Hagen Ulltveit-Moe
# Licensed under the LGPL, see <http://www.gnu.org/licenses/>

import platform
import _dragonfly_utils as utils

from dragonfly import (
    Key,
    Mimic,
    IntegerRef,
)
# Ordered list of pinned taskbar items. Sublists refer to windows within a specific application.
windows = [
    "browse",
    "storm",
    "code",
    "charm",
    "source",
    "email", # 6
    "slack", # 7
    "explore",
    "text",
]

outlook_n = "6"
slack_n = "7"

windows_prefix = "go"
windows_mapping = {}
for i, window in enumerate(windows):
    if isinstance(window, str):
        window = [window]
    for j, words in enumerate(window):
        windows_mapping[windows_prefix + " " + words] = Key("win:down, %d:%d/10, win:up" % (i + 1, j + 1))

windows_prefix_second = "go to"
windows_mapping_second = {}
for i, window in enumerate(windows):
    if isinstance(window, str):
        window = [window]
    for j, words in enumerate(window):
        windows_mapping_second[windows_prefix_second + " " + words] = Key(
            "win:down, %d:%d/10, %d:%d/10, win:up" % (i + 1, j + 1, i + 1, j + 1))


# Work around security restrictions in Windows 8.
if platform.release() == "8":
    swap_action = Mimic("press", "alt", "tab")
else:
    swap_action = Key("alt:down, tab:%(n)d/25, alt:up")

final_action_map = utils.combine_maps(windows_mapping, windows_mapping_second, {
    "swap [<n>]":   swap_action,
})

final_element_map = {
    "n": (IntegerRef(None, 1, 5), 1)
}
final_rule = utils.create_rule("FinalRule",
                               final_action_map,
                               final_element_map)


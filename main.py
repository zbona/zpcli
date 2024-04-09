#!/usr/bin/python3

from zpcli import Zpcli
from zpoutput import print_green, print_red, print_yellow, print_gray, print_blue
import sys
import os


def print_status_line(zpcli):
    arg_command, arg_actions, arg_param1, arg_param2 = get_params()
    print(f"ZPCLI ")
    zpcli.process_list_lines(arg_command, arg_param1, arg_param2)
    zpcli.print_list(arg_command, arg_param1, arg_param2)

    print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
    print(f"ZPCLI: ", end="")
    print_yellow(f"{arg_command} {arg_param1} {arg_param2}", False)
    print(">> Filter: ", end="")
    print_yellow(f"{zpcli.C_SEARCH}", False)
    print(" [" + str(len(zpcli.C_SELECTED_COMMAND_ITEMS)) + " rows] Replace: ", end="")
    print_yellow(zpcli.C_REPLACE, False)
    print(" Separator: " + zpcli.C_SEPARATOR, end="")
    print(" Sort: " + zpcli.C_SORT, end="")
    if zpcli.C_MODIFY_COMMAND:
        print_green(" |CONFIRM| ")
    else:
        print_red(" |NOCONFIRM| ")


def main():
    """ main function """
    zpcli = Zpcli()
    config = zpcli.read_conf()
    just_opened = True

    arg_command, arg_actions, arg_param1, arg_param2 = get_params()
    zpcli.params = {
        "arg_command": arg_command,
        "arg_actions": arg_actions,
        "arg_param1": arg_param1,
        "arg_param2": arg_param2
    }
    while True:
        os.system("clear")
        if zpcli.C_LIST_COMMAND:
            arg_command = zpcli.C_LIST_COMMAND
        if zpcli.search_commnad_config(arg_command):
            command_config = zpcli.search_commnad_config(arg_command)
            zpcli.C_COMMANDS = command_config["actions"]
            if just_opened:
                if "separator" in command_config.keys():
                    zpcli.C_SEPARATOR = command_config["separator"]
                if "search" in command_config.keys():
                    zpcli.C_SEARCH = command_config["search"]
                if "replace" in command_config.keys():
                    zpcli.C_REPLACE = command_config["replace"]

        just_opened = False

        zpcli.load_variables()

        print_status_line(zpcli)

        zpcli.print_commands(arg_command)
        action = zpcli.input_action()

        action_key = 0
        if action[0] == "/":
            """ search  """
            zpcli.C_SEARCH = action[1:]
            continue
        elif action.startswith("!"):
            zpcli.C_LIST_COMMAND = action[1:]
            continue
        elif action.startswith("s/"):
            """ sed - substitute """
            zpcli.C_REPLACE = action
            continue
        elif action[0] == ":":
            """ command - separator, save config, record, history, help, edit command """
            # supported_commands = ["help", "save-config", "config", "set", "get", "confirm", "noconfirm", "sep", "sort", "uniq"]
            # if action[1:] not in supported_commands:
            #     print("Command " + action[1:] + " not implemented. Supported commands are:")
            #     print(supported_commands)
            #     input()
            #     continue
            if action[1:] == "help":
                zpcli.action_help()
            elif action[1:].startswith("sort"):
                zpcli.C_SORT = action.replace(":sort ", "")
                continue
            elif action[1:] == "uniq":
                zpcli.action_uniq()
            elif action[1:] == "save-config":
                zpcli.action_save_config()
            elif action[1:] == "config":
                os.system("vim " + zpcli.config_file)
                zpcli.read_conf()
            elif action[1:].startswith("get"):
                print(zpcli.C_VARIABLES)
                input()
            elif action[1:].startswith("set "):
                variable_tmp = action.replace(":set ", "").strip()
                variable = variable_tmp.split("=")
                zpcli.save_variable(variable[0], variable[1])
                print(zpcli.C_VARIABLES)
                input()
            elif action[1:] == "confirm":
                zpcli.C_MODIFY_COMMAND = True
            elif action[1:] == "noconfirm":
                zpcli.C_MODIFY_COMMAND = False
            elif action[1:].startswith("sep"):
                separator = action[1:].split("=", maxsplit=1)[1]
                if not separator:
                    separator = zpcli.C_SEPARATOR_DEFAULT
                zpcli.C_SEPARATOR = separator
            continue
        elif action[0] == "+":
            """ add action command to runtime """
            zpcli.add_action_command(action[1:])
            continue
        elif action[0] == "!":
            """ modify command befire run """
            zpcli.C_MODIFY_COMMAND = True
            action_key = int(action[1:])
        elif action[0] == "q":
            """ exit """
            sys.exit()
        else:
            """ run normal action """
            action_key = action

        items = zpcli.input_items()
        if items[0] == "q":
            sys.exit()

        if items == ["*"]:
            zpcli.C_LAST_ITEM = []
            items = []
            for i in zpcli.C_SELECTED_COMMAND_ITEMS.keys():
                items.append(i)
                zpcli.C_LAST_ITEM.append(str(i))
        # print("items")
        # print(items)
        zpcli.save_variable("SUM", 0)

        for item_key in items:
            try:
                zpcli.run_command(action_key, item_key)
            except Exception as exc:
                print(exc)

        print("... press Enter to continue ...")
        x = input()


def get_params():
    arg_command = sys.argv[1]
    if len(sys.argv) > 2:
        arg_actions = sys.argv[2]
    else:
        arg_actions = ""

    if len(sys.argv) > 3:
        arg_param1 = sys.argv[3]
    else:
        arg_param1 = ""

    if len(sys.argv) > 4:
        arg_param2 = sys.argv[4]
    else:
        arg_param2 = ""

    return arg_command, arg_actions, arg_param1, arg_param2


if __name__ == "__main__":
    main()

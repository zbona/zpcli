#!python3

from zpcli import Zpcli
from zpoutput import print_green, print_red, print_yellow, print_gray, print_blue
import sys
import os
from rich import print
from rich import box
from rich.style import Style
from rich.color import Color
from rich.color import ColorType
from rich.panel import Panel


def print_list_items(zpcli):
    arg_command, arg_actions, arg_param1, arg_param2 = get_params(zpcli)
    zpcli.process_list_lines(arg_command, arg_param1, arg_param2)
    zpcli.print_list(arg_command, arg_param1, arg_param2)


def print_status_line(zpcli):
    arg_command, arg_actions, arg_param1, arg_param2 = get_params(zpcli)
    # panel_content = f"ZPCLI: "
    panel_content = ""
    panel_content = panel_content + f">> [bold][yellow]{arg_command} {arg_param1} {arg_param2}[/yellow][/bold]"
    panel_content = panel_content + f">> Filter: "
    panel_content = panel_content + f"{zpcli.C_SEARCH}"
    panel_content = panel_content + f" [" + str(len(zpcli.C_SELECTED_COMMAND_ITEMS)) + " rows] Replace: [yellow]" + zpcli.C_REPLACE + "[/yellow]"
    panel_content = panel_content + f" Separator: " + zpcli.C_SEPARATOR
    panel_content = panel_content + f" Sort: " + zpcli.C_SORT
    if zpcli.C_MODIFY_COMMAND:
        panel_content = panel_content + (" [green]|CONFIRM|[/green] ")
    else:
        panel_content = panel_content + (" [red]|CONFIRM|[/red] ")
    style = "border green"
    print(Panel(panel_content, title="(ZPCLI)", title_align="left", box=box.HORIZONTALS, border_style="deep_pink4"))


def main():
    """ main function """
    zpcli = Zpcli()
    config = zpcli.read_conf()
    just_opened = True

    arg_command, arg_actions, arg_param1, arg_param2 = get_params(zpcli)
    if arg_command == "":
        arg_command = "grep list-command " + zpcli.config_file
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
            init_config(zpcli, arg_command, just_opened)
        just_opened = False

        zpcli.load_variables()

        # print_status_line(zpcli)
        print_list_items(zpcli)
        print_status_line(zpcli)

        zpcli.print_commands(arg_command)
        action = zpcli.input_action().strip()

        zpcli.C_TMUX_SPLIT = False
        action_key = 0
        if action.startswith( "//" ):
            """ search  """
            zpcli.C_ACTION_SEARCH = action[2:]
            continue
        elif action[0] == "/":
            """ search  """
            zpcli.C_SEARCH = action[1:]
            continue
        elif action.startswith("!"):
            zpcli.C_LIST_COMMAND = action[1:]
            continue
        elif action.startswith(":s/"):
            """ sed - substitute """
            zpcli.C_REPLACE = action[1:]
            continue
        elif action[0] == ":":
            zpcli_commands(zpcli, action)
            continue
        elif action[0] == "+":
            """ add action command to runtime """
            zpcli.add_action_command(action[1:])
            continue
        elif action[0] == "-":
            """ add action command to runtime """
            zpcli.remove_action_command(action[1:])
            continue
        elif action[0] == "%":
            """ add action command to runtime """
            zpcli.C_TMUX_SPLIT = True
            action_key = action[1:]
        elif action[0] == "?":
            """ add action command to runtime """
            commands = zpcli.search_commnad_config(arg_command)["actions"]
            print(commands[int(action[1:]) - 1])
            print( "... Press Enter to continue ...")
            AAA = input()
            continue
        elif action[0] == "!":
            """ modify command befire run """
            zpcli.C_MODIFY_COMMAND = True
            action_key = int(action[1:])
        elif action == "q":
            """ exit """
            sys.exit()
        else:
            if action.isnumeric():
                """ run normal action """
                action_key = action
            else:
                zpcli.run_system(action)
                print("... press Enter to continue ...")
                input()
                continue

        current_command = zpcli.C_COMMANDS[int(action_key) - 1]

        ask_for_items = True
        if type(current_command) is dict and "loop_command" in current_command and current_command["loop_command"].find("$") == -1:
            ask_for_items = False
        elif type(current_command) is str and current_command.find("$") == -1:
            ask_for_items = False
            
        # don't ask items if variable is not used in the command
        if ask_for_items:
            items = zpcli.input_items()
            if items[0] == "q":
                sys.exit()

            if items == ["*"]:
                zpcli.C_LAST_ITEM = []
                items = []
                for i in zpcli.C_SELECTED_COMMAND_ITEMS.keys():
                    items.append(i)
                    zpcli.C_LAST_ITEM.append(str(i))
        else:
            items = [1]

        zpcli.C_VARIABLE_CONFIRMED = False
        before_command_cmd, loop_command_cmd, after_command_cmd = zpcli.get_command_by_index(action_key)

        if before_command_cmd != "":
            print("Running command before:")
            print("> " + before_command_cmd)
            output = os.system(before_command_cmd)
            print(output)

        for item_key in items:
            try:
                can_continue = zpcli.run_command(loop_command_cmd, item_key)
                if can_continue == False:
                    break
                else:
                    zpcli.C_VARIABLE_CONFIRMED = True
            except Exception as exc:
                print(exc)

        if after_command_cmd != "":
            print("Running command after:")
            print("> "+ after_command_cmd)
            output = os.system(after_command_cmd)
            print(output)

        print("... press Enter to continue ...")
        x = input()


def print_list(mydict):
    print("\n".join("{} = {}".format(k, v) for k, v in sorted(mydict.items(), key=lambda t: str(t[0]))))


def zpcli_commands(zpcli, action):
    """ command - separator, save config, record, history, help, edit command """
    if action[1:] == "help":
        zpcli.action_help()
    elif action[1:].startswith("sort"):
        zpcli.C_SORT = action.replace(":sort ", "")
    elif action[1:] == "uniq":
        zpcli.action_uniq()
    elif action[1:] == "save-config":
        zpcli.action_save_config()
    elif action[1:] == "config":
        os.system("vim " + zpcli.config_file)
        zpcli.read_conf()
    elif action[1:] == "var":
        os.system("vim " + zpcli.variable_file)
        zpcli.load_variables()
    elif action[1:].startswith("get"):
        print_list(zpcli.C_VARIABLES)
        input()
    elif action[1:].startswith("set-local"):
        variable_tmp = action.replace(":set-local ", "").strip()
        variable = variable_tmp.split("=")
        zpcli.C_VARIABLES_LOCAL[variable[0]] = variable[1]
    elif action[1:].startswith("set "):
        variable_tmp = action.replace(":set ", "").strip()
        variable = variable_tmp.split("=", 1)
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
    elif action[1:].startswith("cd "):
        cd_parts = action[1:].split(" ")
        os.chdir(cd_parts[1])
    elif action[1:] == "pwd":
        print(os.getcwd())
        input()


def init_config(zpcli, arg_command, just_opened):
    command_config = zpcli.search_commnad_config(arg_command)
    zpcli.C_COMMANDS = command_config["actions"]
    if just_opened:
        if "separator" in command_config.keys():
            zpcli.C_SEPARATOR = command_config["separator"]
        if "search" in command_config.keys():
            zpcli.C_SEARCH = command_config["search"]
        if "replace" in command_config.keys():
            zpcli.C_REPLACE = command_config["replace"]
        if "modify" in command_config.keys():
            if command_config["modify"] == "1":
                zpcli.C_MODIFY_COMMAND = True
            else:
                zpcli.C_MODIFY_COMMAND = False

def get_params(zpcli):
    if zpcli.C_LIST_COMMAND:
        arg_command = zpcli.C_LIST_COMMAND
    else:
        if len(sys.argv) > 1:
            arg_command = sys.argv[1]
        else:
            arg_command = "grep list-command " + zpcli.config_file
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

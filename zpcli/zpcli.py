import os
import subprocess
import re
import sys

import yaml
from zpoutput import print_green, print_red, print_yellow, print_gray, print_blue, rlinput
from rich.table import Table
from rich.console import Console
import readline

import logging

LOG_FILENAME = '/tmp/completer.log'
logging.basicConfig(filename=LOG_FILENAME,
                    level=logging.DEBUG,
                    )


class Zpcli:
    C_LIST_COMMAND = ""
    C_COMMAND_ITEMS = {}
    C_SELECTED_COMMAND_ITEMS = {}
    C_REPLACED_COMMAND_ITEMS = []
    C_COMMANDS = []
    C_ADDED_COMMANDS = []
    C_SEARCH = ""
    C_REPLACE = ""
    C_SEPARATOR = r"\s+"
    C_SEPARATOR_DEFAULT = r"\s+"
    C_CONFIRM = False
    C_LAST_ACTION = "/"
    C_LAST_ITEM = []
    C_MODIFY_COMMAND = False
    C_VARIABLES = {}
    C_VARIABLES_LOCAL = {}
    C_SORT = ""
    C_ZPCLI_COMMANDS = [":help", ":set", ":set-local", ":get", ":sort", ":sep=", ":confirm", ":save-config", "q",
                        ":noconfirm", ":config", "/", "s//", "+cat $1"]
    CONFIG = {}
    config_file = ""
    variable_file = ""
    params = {}

    def __init__(self):
        """ init """
        self.config_file = os.path.expanduser("~") + "/.zpcli.yaml"
        self.variable_file = os.path.expanduser("~") + "/.zpcli-vars.yaml"

    def zpcli_complete(self, text, state):
        """ """
        line = readline.get_line_buffer().split()

        results = []
        if line[0] == ":set" or line[0] == ":set-local":
            # logging.debug("line", line)
            variable_name = line[1]
            # logging.debug("variavle", variable_name)
            for c in self.C_VARIABLES:
                if c.startswith(variable_name):
                    results.append(line[0] + " " + c)
        else:
            results = [c + ' ' for c in self.C_ZPCLI_COMMANDS if c.startswith(line[0].strip())]

        logging.debug("text %s", text)
        logging.debug("state %s", state)
        return results[state]

    def input_action(self):
        """ input actio """
        print_yellow(
            "\"Type \"q\" to quit; type \"/<string>\" to filter list; \":help\" to more information")
        print_red("Action ", False)
        print_gray(" - Press ENTER to use last action ", False)
        print_red("\[" + self.C_LAST_ACTION + "]: ", False)

        readline.set_completer_delims('\t')
        readline.parse_and_bind("tab: complete")

        readline.set_completer(self.zpcli_complete)

        action = input()

        print(action)

        if action == "":
            action = self.C_LAST_ACTION
        else:
            self.C_LAST_ACTION = action
        return action

    def get_params(self):
        return self.params["arg_command"], self.params["arg_actions"], self.params["arg_param1"], self.params[
            "arg_param2"]

    def input_items(self):
        """ input itens """
        print_green("Item: ", False)
        print_gray(" - press Enter to use last", False)
        print_green(" [" + str(self.C_LAST_ITEM) + "]: ", False)
        item = input()
        if str(item).find("-") != -1:
            range_arr = item.split("-")
            item = ""
            it = range(int(range_arr[0]), int(range_arr[1]) + 1)
            print(it)
            for i in it:
                item = item + " " + str(i)
        if item == "":
            item = " ".join(self.C_LAST_ITEM)
            print()
        else:
            self.C_LAST_ITEM = item.split(" ")
        item = item.strip()
        print(item)
        return item.split(" ")

    def add_action_command(self, command):
        """ set column separator """
        self.C_COMMANDS.append(command)
        self.C_ADDED_COMMANDS.append(command)

    def search_commnad_config(self, list_command):
        for lc in self.CONFIG["commands"]:
            if lc["list-command"] == list_command:
                return lc
        command = {"list-command": list_command, "actions": ["aaa"]}
        self.CONFIG["commands"].append(command)
        return command

    def action_sort(self, column):
        # print(self.C_SORT)
        if column == "0":
            return
        # print(column)
        column_abs = abs(int(column))
        # print(column_abs)
        # print(column_abs - 1)
        dict_to_sort = {}
        for i in self.C_SELECTED_COMMAND_ITEMS:
            cols = re.split(rf"{self.C_SEPARATOR}", self.C_SELECTED_COMMAND_ITEMS[i])
            # print(cols)
            if len(cols) >= column_abs:
                my_col = cols[int(column_abs - 1)]
            else:
                # print(cols)
                my_col = ""
                continue
            if my_col.isnumeric():
                dict_to_sort[i] = int(my_col)
            else:
                dict_to_sort[i] = my_col

        if int(column) < 0:
            sorted_column = sorted(dict_to_sort.items(), key=lambda x: x[1], reverse=True)
        else:
            sorted_column = sorted(dict_to_sort.items(), key=lambda x: x[1])

        sorted_lines = {}
        for sorted_key in sorted_column:
            sorted_lines[sorted_key[0]] = self.C_SELECTED_COMMAND_ITEMS[sorted_key[0]]

        self.C_SELECTED_COMMAND_ITEMS = sorted_lines

    def action_uniq(self):
        """  """

    def load_variables(self):
        os.system("touch " + self.variable_file)
        try:
            with open(self.variable_file, "r") as file:
                vars = yaml.safe_load(file)
                if vars:
                    self.C_VARIABLES = vars
        except yaml.YAMLError as exc:
            print(exc)
        for var in self.C_VARIABLES_LOCAL:
            self.C_VARIABLES[var] = self.C_VARIABLES_LOCAL[var]

    def get_list_command_output(self, list_command, param1, param2):

        if list_command.startswith("ssh "):
            ssh_args = list_command[4:].split('"')
            ssh = subprocess.run(["ssh", ssh_args[0].strip(), ssh_args[1].strip()],
                                 shell=False,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            return str(ssh.stdout.decode("utf-8")).splitlines()

        list_command_arr = list_command.split(" ")
        if param1:
            param1_arr = param1.split(" ")
            for p1 in param1_arr:
                list_command_arr.append(p1)
        if param2:
            param2_arr = param2.split(" ")
            for p2 in param2_arr:
                list_command_arr.append(p2)
        try:
            process = subprocess.Popen(list_command_arr, stdout=subprocess.PIPE)
            output = process.communicate()[0].decode("utf-8")
            outputLines = output.split(os.linesep)
        except Exception as ex:
            outputLines = []
            print(ex)
        return outputLines

    def process_list_lines(self, list_command, param1, param2):
        outputLines = self.get_list_command_output(list_command, param1, param2)

        self.C_COMMAND_ITEMS = {}
        current_lines = {}

        i = 1
        for line in outputLines:
            """   """
            if not line:
                continue
            if self.C_REPLACE:
                tmpreplace = self.C_REPLACE.replace("\/", "[escaped-slash]")
                replace_list = tmpreplace.split("/")
                if re.match(".*" + replace_list[1].replace("[escaped-slash]", "/") + ".*", line) is not None:
                    line = re.sub(replace_list[1].replace("[escaped-slash]", "/"),
                                  replace_list[2].replace("[escaped-slash]", "/"), line)
                    self.C_REPLACED_COMMAND_ITEMS.append(i)
            if self.C_SEARCH != "":
                match_search = re.match(".*" + self.C_SEARCH + ".*", line)
                if match_search:
                    current_lines[i] = line
            else:
                current_lines[i] = line
            self.C_COMMAND_ITEMS[i] = line
            i = i + 1

        self.C_SELECTED_COMMAND_ITEMS = current_lines

        if self.C_SORT and self.C_SORT != "0":
            self.action_sort(self.C_SORT)

    def save_variable(self, var, val):
        self.C_VARIABLES[var] = val

        with open(self.variable_file, "w") as var_file:
            var_file.write(yaml.dump(self.C_VARIABLES))

    def print_list_rich(self):
        console = Console()
        table = Table(show_header=True, header_style="bold magenta")
        for i in range(len(self.C_SELECTED_COMMAND_ITEMS[1])):
            table.add_column(str(i))

        print(self.C_SELECTED_COMMAND_ITEMS[1])
        cols = re.split(rf"{self.C_SEPARATOR}", self.C_SELECTED_COMMAND_ITEMS[2])
        print(cols)
        table.add_row(cols)

        console.print(table)
        sys.exit()
        for row in self.C_SELECTED_COMMAND_ITEMS:
            cols = re.split(rf"{self.C_SEPARATOR}", row)
            table.add_row(**cols)

        console.print(table)

    def print_list(self, list_command, param1, param2):
        """ print list """
        print("================================================")
        config_command = self.search_commnad_config(list_command)

        for i in self.C_SELECTED_COMMAND_ITEMS:
            line = self.C_SELECTED_COMMAND_ITEMS[i]
            if i in self.C_REPLACED_COMMAND_ITEMS:
                star = "*"
            else:
                star = " "
            if str(i) in self.C_LAST_ITEM:
                print_green(star + str(i) + ": " + line)
            else:
                print_green(star + str(i) + ": ", False)
                print(" " + line)

    def print_commands(self, list_command):
        commands = self.search_commnad_config(list_command)["actions"]
        """ print defined commands """
        print("================================================")

        for index, command in enumerate(commands):
            if command in self.C_ADDED_COMMANDS:
                star = "*"
            else:
                star = " "
            if str(index + 1) == self.C_LAST_ACTION:
                print_red(star + str(index + 1) + ") " + command)
            else:
                print_red(star + str(index + 1) + ") ", False)
                print(command)

    def run_command(self, command_key, item_key):
        """ run command """
        print_yellow("vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv")

        command_num = int(command_key)
        run_cmd = str(self.C_COMMANDS[command_num - 1]).strip()

        arg_command, arg_actions, arg_param1, arg_param2 = self.get_params()
        # replace zpcli params to action command
        run_cmd = run_cmd.replace("$param1", arg_param1)
        run_cmd = run_cmd.replace("$param2", arg_param2)

        # selected_items_array = {}
        # print(self.C_SELECTED_COMMAND_ITEMS)
        # for si in self.C_SELECTED_COMMAND_ITEMS:
        #     print('xxx')
        #     for ii in range(1, 20):
        #         print('yyy')
        #         print(si)
        #         print(ii)
        #         selected_items_array[ii][si] = self.get_selected_items_col(si, ii - 1)
        #         print(selected_items_array)

        can_continue = True
        # print('aaa')
        # print(selected_items_array)
        for i in range(1, 20):
            selected_item = self.get_selected_items_col(item_key, i - 1)
            if selected_item != "" and selected_item is not None:
                run_cmd = run_cmd.replace("$" + str(i), selected_item)
                # all chosen rows as command params
                # if run_cmd.find("$$" + str(i)) != -1:
                #     run_cmd = run_cmd.replace(" $$" + str(i), " ".join(selected_items_array[i]))
                #     can_continue = False
            else:
                run_cmd = run_cmd.replace(" $" + str(i), "")

        for key in self.C_VARIABLES:
            # print(key)
            run_cmd = run_cmd.replace("$" + key, str(self.C_VARIABLES[key]))

        run_cmd = run_cmd.replace("=>", "; ")

        if self.C_VARIABLES["command-wrapper"] and self.C_VARIABLES["cw-enabled"]:
            run_cmd = self.C_VARIABLES["command-wrapper"].replace("<command>", run_cmd)

        # print(self.C_VARIABLES["SUM"])
        print_blue(run_cmd)
        if self.C_MODIFY_COMMAND:
            run_cmd = rlinput("> ", run_cmd)

        if self.C_CONFIRM:
            print_red("Realy run: " + run_cmd + " ? y/n")
            confirm = input()
        else:
            confirm = "y"

        if confirm == "y":
            # process = subprocess.run(command_arr, cwd="/home")
            if run_cmd.startswith("ssh ") and run_cmd.find('"') != -1:
                ssh_args = run_cmd[4:].split('"')
                ssh = subprocess.run(["ssh", ssh_args[0].strip(), ssh_args[1].strip()],
                                     shell=False,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
                output = str(ssh.stdout.decode("utf-8"))
            else:
                output = os.system(run_cmd)

            print(output)
            return can_continue

    def action_save_config(self):
        conf_file = self.config_file
        with open(conf_file, "w") as config_file:
            config_file.write(yaml.dump(self.CONFIG))
        print("config saved... press Enter...")
        x = input()

    def action_help(self):
        help = f"""HELP
==================================================================================================================
ZPCLI:
- interactive command executing/scripting for table outputs
- get / modify output, define bash actions, select action and items to be used for that action

ACTIONS:
:help           this output
:config         open yaml config in vim editor
:sep=,          change cols separator from default "\s+" to "," (e.g. for csv)
:confirm        command needs to be confirmed before execution, you can also modify it
:noconfirm      default - command executed without confirmation
:sort 2         sort list by 2nd column (asc)
:sort -2        sort listy by 2nd column (desc)
:sort 0         disable sorting
4               run action "4)"
/mystr          search 'mystr' string in the output
/               remove filter
s/search/repl   'search' will be replaced by 'repl' in the output
s//             remove/reset replacement
:set var=value  set global variable called "var" with "value" as value. You can use it in your commands as $var then
:set-local v=x  set LOCAL variable called "v" with "x" as value. This value is used just for current zpcli instance
:get            get all set variables
+cat $1 $2 $var action command will be added to commands taken from yaml configuration (just for this time)
                $1 - will be replaced by value in 1st column of selected item(s)
                $2 - will be replaced by value in 2nd column of selected item(s)
                $var - will be replaced by value od var variable (see above)
:save-config    save current config - adds new commands added above permanently
q               quit zpcli 

ITEMS:
12              run action for item "12:"
1 3 5           run action for multiple items (lines "1:", "3:", "5:")
*               run action for all displayed / filtered items

!ls -la         change list command to any other

... press Enter to continue ...
"""

        print(help)
        x = input()

    def read_conf(self):
        """ read configuration """
        try:
            with open(self.config_file, "r") as file:
                config = yaml.safe_load(file)
        except yaml.YAMLError as exc:
            print(exc)
        self.CONFIG = config
        return config

    def get_selected_items_col(self, item_number, col_number):
        result = {}
        result_string = ""
        if not item_number:
            return ""
        ic_int = int(item_number)
        if self.C_COMMAND_ITEMS[ic_int]:
            cols = re.split(rf"{self.C_SEPARATOR}", self.C_COMMAND_ITEMS[ic_int])
            result[ic_int] = cols
            if len(cols) > col_number:
                result_string = result_string + " " + cols[col_number]

        return result_string.strip()

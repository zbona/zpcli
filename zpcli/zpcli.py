from curses.ascii import EM, isdigit
import os
import subprocess
import re
import sys
import shutil

import yaml
from zpoutput import print_green, print_red, print_yellow, print_gray, print_blue, get_highlighted, rlinput
from rich.table import Table
from rich.console import Console
from rich.columns import Columns
from rich.theme import Theme
from rich.panel import Panel
from rich import box
from rich.markup import escape
import gnureadline as readline
import pyfzf

import logging
from rich import print


LOG_FILENAME = '/tmp/completer.log'
logging.basicConfig(filename=LOG_FILENAME,
                    level=logging.DEBUG,
                    )

zpcli_highlight = Theme({
    "zpcli_er": "black on orange_red1",
    "zpcli_wa": "black on yellow1",
    "zpcli_ok": "black on green3",
})

class Zpcli:
    C_LIST_COMMAND = ""
    C_LIST_COMMAND_NAME = ""
    C_COMMAND_ITEMS = {}
    C_SELECTED_COMMAND_ITEMS = {}
    C_REPLACED_COMMAND_ITEMS = []
    C_COMMANDS = []
    C_ADDED_COMMANDS = []
    C_ACTION_SEARCH = ""
    C_SEARCH = ""
    C_REPLACE = ""
    C_SEPARATOR = r"\s+"
    C_SEPARATOR_DEFAULT = r"\s+"
    C_CONFIRM = False
    C_VARIABLE_CONFIRMED = False
    C_LAST_ACTION = "/"
    C_LAST_ITEM = []
    C_MODIFY_COMMAND = False
    C_TMUX_SPLIT = False
    C_VARIABLES = {}
    C_VARIABLES_LOCAL = {}
    C_SORT = ""
    C_ZPCLI_COMMANDS = [":help", ":set", ":set-local", ":get", ":sort", ":sep=", ":confirm", ":save-config", "q",
                        ":cd", ":pwd", ":var"
                        ":noconfirm", ":config", "/", ":s//", "+cat $1"]
    AI_SUMARIZE = True
    CONFIG = {}
    config_file = ""
    variable_file = ""
    history_file = ""
    params = {}

    def __init__(self):
        """ init """
        self.config_file = os.path.expanduser("~") + "/.zpcli.yaml"
        self.variable_file = os.path.expanduser("~") + "/.zpcli-vars.yaml"
        readline.read_history_file(os.path.expanduser("~") + '/.bash_history')
        self.history_file = os.path.expanduser("~") + '/.bash_history'


    def list_folder(self, path):
        """
        Lists folder contents
        """
        if path.startswith(os.path.sep):
            # absolute path
            basedir = os.path.dirname(path)
            contents = os.listdir(basedir)
            # add back the parent
            contents = [os.path.join(basedir, d) for d in contents]
        else:
            # relative path
            contents = os.listdir(os.curdir)

        return contents


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
        elif line[0] == ":cd":
            my_path = line[1]
            results = [':cd ' + x for x in self.list_folder(my_path) if x.startswith(my_path.strip())]
        else:
            results = [c for c in self.C_ZPCLI_COMMANDS if c.startswith(" ".join(line).strip())]

        logging.debug("text %s", text)
        logging.debug("state %s", state)
        return results[state]

    def input_action_fzf(self):
        all_actions = self.get_comands_dict() #  (self.C_ZPCLI_COMMANDS)
        prompt_options = []
        for my_action in all_actions:
            item = str(my_action) + ") " + all_actions[my_action]
            prompt_options.append(item)

        fzf = pyfzf.FzfPrompt()
        action = fzf.prompt(prompt_options, fzf_options='--height 5 --layout=reverse')

        if not action:
          return_action = ""
        elif isdigit(action[0][0]):
          tmp = action[0][0].split(")", 1)
          return_action = tmp[0]
        else:
          return_action = action[0]
        return return_action

    def input_action(self):
        """ input action """
        print_yellow(
            "\"Type \"q\" to quit; type \"/<string>\" to filter list; \"//string\" to filter command; \":help\" to more information")
        print("> " + os.getcwd())
        print_red("Action ", False)
        print_gray(" - Press ENTER to use last action ", False)
        print_red("\[" + self.C_LAST_ACTION + "]: ")

        # readline.set_completer_delims(' \t\n')
        readline.parse_and_bind("tab: complete")

        with open(self.history_file, "r") as h_file:
            history_lines = h_file.readlines()

        for history_line in history_lines:
            if history_line not in self.C_ZPCLI_COMMANDS:
                self.C_ZPCLI_COMMANDS.append(str(history_line).strip())

        readline.set_completer(self.zpcli_complete)
        readline.set_completer_delims('')
        # readline.set_completer_delims(' \t\n')

        action = input()

        if action == "":
            action = self.C_LAST_ACTION
        elif action != " ":
            self.C_LAST_ACTION = action
        return action


    def get_comands_dict(self):
        # print(self.C_COMMANDS)
        my_dict = {}
        i = 1
        for commnd in self.C_COMMANDS:
            if "loop_command" in self.C_COMMANDS[int(i-1)]:
                my_dict[str(i)] = commnd["loop_command"]
            else:
                my_dict[str(i)] = commnd
            i = i + 1
        return my_dict


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
        if item == " ":
            item = self.select_item(self.C_COMMAND_ITEMS)
            # print(item)
            # sys.exit()
            print()
        elif item == "":
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

    def remove_action_command(self, command):
        """ set column separator """
        self.C_COMMANDS.remove(command)
        self.C_ADDED_COMMANDS.append(command)

    def search_commnad_config(self, list_command):
        for lc in self.CONFIG["commands"]:
            if "name" in lc and lc["name"] == list_command:
                self.C_LIST_COMMAND_NAME = list_command
                return lc
            if "name" in lc and lc["name"] == self.C_LIST_COMMAND_NAME:
                return lc
        for lc in self.CONFIG["commands"]:
            if lc["list-command"] == list_command:
                return lc
        command = {"list-command": list_command, "actions": ["Not found"]}
        self.CONFIG["commands"].append(command)
        return command

    def replace_command_config(self):
        for i in range(len(self.CONFIG["commands"])):
            if self.CONFIG["commands"][i]["list-command"] == self.C_LIST_COMMAND:
                self.CONFIG["commands"][i]["replace"] = str(self.C_REPLACE)
                self.CONFIG["commands"][i]["separator"] = str(self.C_SEPARATOR)
                self.CONFIG["commands"][i]["search"] = str(self.C_SEARCH)

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

        if list_command.find("$list-param1") != -1:
            list_command = list_command.replace("$list-param1", self.C_VARIABLES["list-param1"])
        if list_command.find("$list-param2") != -1:
            list_command = list_command.replace("$list-param2", self.C_VARIABLES["list-param2"])

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
            # process2 = subprocess.Popen(["grep", "-t"], stdin=process.stdout, stdout=subprocess.PIPE)
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
                replace_strings = self.C_REPLACE.split("&&")
                for replace_string in replace_strings:
                    tmpreplace = replace_string.replace("\/", "[escaped-slash]")
                    replace_list = tmpreplace.split("/")
                    if re.match(".*" + replace_list[1].replace("[escaped-slash]", "/") + ".*", line) is not None:
                        line = re.sub(replace_list[1].replace("[escaped-slash]", "/"),
                                      replace_list[2].replace("[escaped-slash]", "/"), line)
                        self.C_REPLACED_COMMAND_ITEMS.append(i)

            if self.C_SEARCH != "":
                match_search_present = False
                match_search_absent = True
                if self.C_SEARCH.find("^") != -1:
                    my_search = self.C_SEARCH.split("^")
                else:
                    my_search = [self.C_SEARCH, ""]

                if my_search[0] == "":
                    match_search_present = True
                elif my_search[0].find("|") != -1:
                    matched_words = my_search[0].split("|")
                    for word in matched_words:
                        if line.find(word) != -1:
                            match_search_present = match_search_present or True
                            # break
                else:
                    match_search_present = bool(re.match(".*" + my_search[0] + ".*", line))

                if my_search[1] != "":
                    not_matched_words = my_search[1].split("|")
                    for word in not_matched_words:
                        if line.find(word) != -1:
                            match_search_absent = match_search_absent and False


                if match_search_present and match_search_absent:
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


    def print_list(self, list_command, param1, param2):
        """ print list """
        config_command = self.search_commnad_config(list_command)

        items_list = []

        for i in self.C_SELECTED_COMMAND_ITEMS:
            line = self.C_SELECTED_COMMAND_ITEMS[i]
            line = line.replace("\t", " ")
            if i in self.C_REPLACED_COMMAND_ITEMS:
                star = ":brown_circle:"
            else:
                star = ""
            if str(i) in self.C_LAST_ITEM:
                items_list.append("[orange_red1]" + star + str(i) + "[/orange_red1]" + ": " + line)
            else:
                items_list.append("[green3]" + star + str(i) + "[/green3] " + line)
        title = "(ZPCLI)"
        subtitle = list_command + " --- /" + self.C_SEARCH
        print(Panel("\n".join(items_list), title=f"{title} --- {subtitle}", title_align="left", border_style="deep_pink4"))

    def print_commands(self, list_command):
        commands = self.search_commnad_config(list_command)["actions"]
        """ print defined commands """

        console = Console()

        def cmd_detail(command, command_key):
            lines = command.splitlines()
            cmd = command

            color = "orange_red1"
            if cmd.startswith("*"):
                color = "deep_pink4"
            # if command.startswith("#"):
            if self.C_ACTION_SEARCH == "" and len(lines) > 1:
                cmd = lines[0]
            elif self.C_ACTION_SEARCH == "" and len(cmd) > 50:
                # cmd = cmd[0:50] + "\n" + cmd[50:]
                cmd = cmd[0:50] + "..."
            return f"[{color}]" + str(command_key) + f")[/{color}] " + cmd + " "

        commands_cols = [] # [Panel(xxx(p_cmd), expand = True) for p_cmd in commands]
        for key, val in enumerate(commands):
            if "loop_command" in val:
                command = val["loop_command"]
            else:
                command = val
            # commands_cols.append( Panel(cmd_detail( title ), expand=True, padding=[-1, -1], box=box.MINIMAL))
            if self.C_ACTION_SEARCH != "" and command.find(self.C_ACTION_SEARCH) == -1:
                continue
            # rewrite command by it's title if it is set
            if self.C_ACTION_SEARCH == "" and "title" in val:
                command = "*" + val["title"]
            command_key = key + 1
            commands_cols.append( cmd_detail( command, command_key))
        title = "Commnads //" + self.C_ACTION_SEARCH
        print(Panel(Columns(commands_cols, expand=True, padding = [0,0]), title=f"{title}", title_align="left", border_style="orange_red1"))


    def run_system(self, action):
        os.system(action)
        if len(action) > 2:
            readline.write_history_file(self.history_file)

    def get_command_by_index(self, command_key):
        command_num = int(command_key)
        run_cmd_c = self.C_COMMANDS[command_num - 1]

        if type(run_cmd_c) is dict:
            if "before_command" in run_cmd_c:
                before_command_cmd = run_cmd_c["before_command"]
            else:
                before_command_cmd = ""
            if "after_command" in run_cmd_c:
                after_command_cmd = run_cmd_c["after_command"]
            else:
                after_command_cmd = ""
            run_cmd = run_cmd_c["loop_command"]
        else:
            before_command_cmd = ""
            after_command_cmd = ""
            run_cmd = run_cmd_c
        run_cmd = str(run_cmd).strip()


        return before_command_cmd, run_cmd, after_command_cmd


    def is_interactive_command(self, command):
        interactive_commands = ["ssh", "kubectl exec -it", "docker exec -it", "vim", "nano", "zpcli", "ping"]
        ssh_pattern = r"ssh\s+\S+@\S+"
        docker_pattern = r"docker exec -it\s+\S+ bash"
        if re.match(ssh_pattern, command) and len(command) > re.match(ssh_pattern, command).end():
            return False
        elif re.match(docker_pattern, command) and len(command) > re.match(docker_pattern, command).end():
            return False
        else:
            for i in interactive_commands:
                if command.find(i) != -1:
                    return True
        return False


    def run_command(self, run_cmd, item_key):
        """ run command """
        print("[deep_pink4]" + ("v" * 100) + "[/deep_pink4]")
        print("[deep_pink4]" + ("=" * 100) + "[/deep_pink4]")


        print(run_cmd)

        arg_command, arg_actions, arg_param1, arg_param2 = self.get_params()
        # replace zpcli params to action command
        run_cmd = run_cmd.replace("$param1", arg_param1)
        run_cmd = run_cmd.replace("$param2", arg_param2)

        can_continue = True

        for i in range(1, 20):
            selected_item = self.get_selected_items_col(item_key, i - 1)
            if selected_item != "" and selected_item is not None:
                run_cmd = run_cmd.replace("$" + str(i), selected_item)
            else:
                run_cmd = run_cmd.replace(" $" + str(i), "")

        for key in self.C_VARIABLES:
            if run_cmd.find("$" + key) != -1:
                if self.C_VARIABLE_CONFIRMED == False:
                    print_red("realy use (y/n)?")
                    print(key + " = " + self.C_VARIABLES[key])
                    x = input()
                    if x != "y":
                        return 0
            run_cmd = run_cmd.replace("$" + key, str(self.C_VARIABLES[key]))

        run_cmd = run_cmd.replace("=>", "; ")
        run_cmd_orig = run_cmd

        input_loop = True
        while input_loop:
            input_loop = False
            print("Run command: " + get_highlighted(run_cmd, '$input'))
            if run_cmd_orig.find("$finput") != -1:
                my_path = ""
                if "filepath" in self.C_VARIABLES:
                    my_input = subprocess.check_output("fzf --preview 'batcat {}'", shell=True, text=True, cwd=self.C_VARIABLES["filepath"])
                    my_input = self.C_VARIABLES["filepath"] + "/" + my_input
                else:
                    my_input = subprocess.check_output("fzf --preview 'batcat {}'", shell=True, text=True)

                if (my_input):
                    run_cmd = run_cmd_orig.replace("$finput", my_input)
                    input_loop = False
            if run_cmd_orig.find("$input") != -1:
                print(get_highlighted("Specify $input", "$input"))
                my_input = input()
                if (my_input):
                    run_cmd = run_cmd_orig.replace("$input", my_input)
                    input_loop = True
                else:
                    input_loop = False
                    return can_continue

            if self.C_VARIABLES["command-wrapper"] and self.C_TMUX_SPLIT == True:
                run_cmd = self.C_VARIABLES["command-wrapper"].replace("<command>", run_cmd)
                print(run_cmd)

            if self.C_CONFIRM:
                print_red("Realy run: " + run_cmd + " ? y/n")
                confirm = input()
            else:
                confirm = "y"

            output = ""
            if confirm == "y":
                try:
                    if self.is_interactive_command(run_cmd):
                        print("run-interactive")
                        subprocess.run(run_cmd, shell=True)
                    else:
                        print("run-get-output")
                        cmd_lines = run_cmd.split("\n")
                        cmd_lines_cnt = len(run_cmd.split("\n"))
                        if cmd_lines_cnt > 1:
                            i = 0
                            while i < cmd_lines_cnt:
                                try:
                                    output = output + "\n>> "  + cmd_lines[i] + "\n"
                                    output = output + subprocess.check_output(cmd_lines[i], shell=True, text=True)
                                except:
                                    pass
                                i = i + 1
                        else:
                            output = subprocess.check_output(run_cmd, shell=True, text=True)
                except:
                    pass

                with open(self.history_file, "a") as f:
                    f.write("\n" + run_cmd)
                readline.add_history(run_cmd)

                subStrings = {
                        # "error": "zpcli_error",
                        "error": "zpcli_er",
                        #"err": "orange_red1",
                        "fail": "zpcli_er",
                        "warn": "zpcli_wa",
                        " ok": "zpcli_ok",
                        #"UP": "zpcli_ok",
                        #"DOWN": "zpcli_error"
                }

                with open("/tmp/zpcli-last-output.log", "w") as f_out:
                    f_out.write(output)

                x =  escape(output) + " "
                for word in subStrings:
                    compiled = re.compile(re.escape(word), re.IGNORECASE)
                    x = compiled.sub(f"[{subStrings[word]}]{word}[/{subStrings[word]}]", x)

                console = Console(theme=zpcli_highlight)
                try:
                    console.print(f"{x}")
                except:
                    print(escape(output))
                    pass
                if self.C_VARIABLES["ai-summary"] == "yes":
                    os.system("ai s /tmp/zpcli-last-output.log")

                if input_loop == False:
                    return can_continue


    def action_save_config(self):
        conf_file = self.config_file
        with open(conf_file, "w") as config_file:
            config_file.write(yaml.dump(self.CONFIG, width=float("inf")))
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
4               run action "4)"
?4              show full command "4)" (without running)
:config         open yaml config in vim editor
:var            open yaml file with variables in vim editor
:cd             change current directory
:pwd            show current directory
:sep=,          change cols separator from default "\s+" to "," (e.g. for csv)
:confirm        command needs to be confirmed before execution, you can also modify it
:noconfirm      default - command executed without confirmation
:sort 2         sort list by 2nd column (asc)
:sort -2        sort listy by 2nd column (desc)
:sort 0         disable sorting
/mystr          search 'mystr' string in the output, by ^ you can filter lines that doesn't containen string ( /^not-this )
/               remove filter
//log           search in commands
//              remove command filter
:s/search/repl   'search' will be replaced by 'repl' in the output, You can multiple replacement by && (:s/s1/r1/ && s/s2/r2/)
:s//             remove/reset replacement
:set var=value  set global variable called "var" with "value" as value. You can use it in your commands as $var then
:set-local v=x  set LOCAL variable called "v" with "x" as value. This value is used just for current zpcli instance
:get            get all set variables
%4              Runs action command 4 wrapped by $command-wrapper variable E.g. open action command in new plitted window in tmux
                :set commapnd-wrapper= tmux split-window -v 'bash -c "<command>"' (<command> will be replaced by action command #4)

+cat $1 $2 $var action command will be added to commands taken from yaml configuration (just for this time)
                $1 - will be replaced by value in 1st column of selected item(s)
                $2 - will be replaced by value in 2nd column of selected item(s)
                $var - will be replaced by value od var variable (see above)
-cat $1 $2 $var action command will be reomved from action list
:save-config    save current config - adds new commands added above permanently
q               quit zpcli

ITEMS:
12              run action for item "12:"
1 3 5           run action for multiple items (lines "1:", "3:", "5:")
*               run action for all displayed / filtered items

!ls -la         change list command to any other
git status      run any bash command, you can also use bash history search by Ctrl+R

... press Enter to continue ...
"""

        print(help)
        x = input()

    def read_conf(self):
        global_config_file = "/usr/local/bin/zpcli/zpcli.yaml"
        """ read configuration """
        if not os.path.isfile(self.config_file):
            if os.path.isfile(global_config_file):
                shutil.copy2(global_config_file, self.config_file)
            else:
                with open(self.config_file, "w") as cf_file:
                    cf_file.write("commands:\n")
                    cf_file.write("- list-command: ls\n")
                    cf_file.write("  actions:\n")
                    cf_file.write("    - cat $1:\n")

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

    def select_item(self, items):
        """
        Umožňuje vybrat více položek ze slovníku pomocí fzf a vrací seznam odpovídajících klíčů.
        Slovník by měl být ve formátu {<int>: <string>}.
        """
        process = subprocess.Popen(['fzf', '-m', '--height=10'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        output, _ = process.communicate('\n'.join(items.values()))
        selected_values = output.strip().split('\n')
        selected_keys = ""
        for key, value in items.items():
          if value in selected_values:
            selected_keys = selected_keys + " " + str(key)
        return selected_keys

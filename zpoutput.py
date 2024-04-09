from colorama import Fore, Back, Style, init
import readline

def print_red(str_to_print, new_line=True):
    if new_line:
        print(f"{Fore.RED}{str_to_print}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}{str_to_print}{Style.RESET_ALL}", end="")


def print_green(str_to_print, new_line=True):
    if new_line == True:
        print(f"{Fore.GREEN}{str_to_print}{Style.RESET_ALL}")
    else:
        print(f"{Fore.GREEN}{str_to_print}{Style.RESET_ALL}", end="")


def print_yellow(str_to_print, new_line=True):
    if new_line == True:
        print(f"{Fore.YELLOW}{str_to_print}{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}{str_to_print}{Style.RESET_ALL}", end="")


def print_blue(str_to_print, new_line=True):
    if new_line == True:
        print(f"{Fore.BLUE}{str_to_print}{Style.RESET_ALL}")
    else:
        print(f"{Fore.BLUE}{str_to_print}{Style.RESET_ALL}", end="")


def print_gray(str_to_print, new_line=True):
    if new_line:
        print(f"{Fore.LIGHTBLACK_EX}{str_to_print}{Style.RESET_ALL}")
    else:
        print(f"{Fore.LIGHTBLACK_EX}{str_to_print}{Style.RESET_ALL}", end="")

def rlinput(prompt, prefill=''):
    readline.set_startup_hook(lambda: readline.insert_text(prefill))
    try:
        return input(prompt)  # or raw_input in Python 2
    finally:
        readline.set_startup_hook()

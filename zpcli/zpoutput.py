from colorama import Fore, Back, Style, init
import readline
from rich import print

def print_red(str_to_print, new_line=True):
    if new_line:
        print(f"[red]{str_to_print}[/red]")
    else:
        print(f"[red]{str_to_print}[/red]", end="")


def print_green(str_to_print, new_line=True):
    if new_line == True:
        print(f"[green]{str_to_print}[/green]")
    else:
        print(f"[green]{str_to_print}[/green]", end="")


def print_yellow(str_to_print, new_line=True):
    if new_line == True:
        print(f"[yellow]{str_to_print}[/yellow]")
    else:
        print(f"[yellow]{str_to_print}[/yellow]", end="")


def print_blue(str_to_print, new_line=True):
    if new_line == True:
        print(f"[blue]{str_to_print}[/blue]")
    else:
        print(f"[blue]{str_to_print}[/blue]", end="")

def get_highlighted(str_to_print: str, str_to_highlight: str):
    str_to_print = str_to_print.replace(str_to_highlight, '[yellow]' + str_to_highlight + '[/yellow]')
    return  str_to_print


def print_gray(str_to_print, new_line=True):
    if new_line:
        print(f"[grey62]{str_to_print}[/grey62]")
    else:
        print(f"[grey62]{str_to_print}[/grey62]", end="")

def rlinput(prompt, prefill=''):
    readline.set_startup_hook(lambda: readline.insert_text(prefill))
    try:
        return input(prompt)  # or raw_input in Python 2
    finally:
        readline.set_startup_hook()

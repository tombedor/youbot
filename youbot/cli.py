import questionary

from youbot.memory import is_context_refresh_needed, refresh_context
from youbot.messenger import user_message
from youbot.store import get_youbot_user_by_id
from colorama import Fore, Style, init
from rich.console import Console

CLI_USER = get_youbot_user_by_id(1)


def main():
    init(autoreset=True)

    console = Console()
    while True:

        user_input = questionary.text("Enter your message:", qmark=">").ask()

        if user_input.startswith("/exit") or user_input == "exit":
            print("Exiting...")
            exit()

        with console.status("[bold cyan]Thinking...") as _status:
            agent_response = user_message(CLI_USER, user_input)

        fstr = f"{Fore.YELLOW}{Style.BRIGHT}🤖 {Fore.YELLOW}{{msg}}{Style.RESET_ALL}"
        print(fstr.format(msg=agent_response))

        if is_context_refresh_needed(CLI_USER):
            refresh_context(CLI_USER)


if __name__ == "__main__":
    main()

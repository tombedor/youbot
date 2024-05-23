import questionary

from youbot.memory import refresh_context_if_needed
from youbot.store import get_youbot_user_by_id
from colorama import Fore, Style, init
from rich.console import Console

from youbot.workers.worker import user_message


if __name__ == "__main__":
    init(autoreset=True)
    youbot_user = get_youbot_user_by_id(1)

    console = Console()
    while True:
        user_input = questionary.text("Enter your message:", qmark=">").ask()

        if user_input.startswith("/exit") or user_input == "exit":
            print("Exiting...")
            exit()

        agent_response = user_message(youbot_user, user_input)

        fstr = f"{Fore.YELLOW}{Style.BRIGHT}🤖 {Fore.YELLOW}{{msg}}{Style.RESET_ALL}"
        print(fstr.format(msg=agent_response))

        refresh_context_if_needed(youbot_user)

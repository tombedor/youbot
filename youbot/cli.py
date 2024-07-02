import questionary

from youbot import CLI_USER_ID
from youbot.messenger import get_ai_reply
from youbot.onboard_user import onboard_user
from youbot.store import maybe_youbot_user_by_id
from colorama import Fore, Style, init
from rich.console import Console
from toolz import pipe

from youbot.workers.worker import context_refresh_async
from functools import partial
from toolz import curry


def exit_cli():
    print("Exiting...")
    exit()


@curry
def process_message_to_ai(console: Console, message: str):
    with console.status("[bold cyan]Thinking...") as _status:
        pipe(
            message,
            get_ai_reply(CLI_USER_ID),
            lambda response: f"{Fore.YELLOW}{Style.BRIGHT}🤖 {Fore.YELLOW}{response}{Style.RESET_ALL}",
            print,
        )
    context_refresh_async.delay(CLI_USER_ID)  # type: ignore


def main():
    init(autoreset=True)

    console = Console()

    maybe_user = maybe_youbot_user_by_id(CLI_USER_ID)
    if maybe_user.is_nothing():
        pipe(
            questionary.text("Welcome to YouBot! What should I call you?", qmark=">").ask(),
            partial(onboard_user, phone=None),
            lambda youbot_user: f"[This is a hidden system message. Youbot user {youbot_user.name} has been onboarded. Say hello and introduce yourself.]",
            process_message_to_ai(console),
        )

    while True:
        try:
            pipe(
                questionary.text("Enter your message:", qmark=">").ask(),
                lambda user_input: (
                    None
                    if not user_input
                    else pipe(
                        user_input,
                        lambda user_input: exit_cli() if user_input.lower().startswith("/exit") or user_input == "exit" else user_input,
                        process_message_to_ai(console),
                    )
                ),
            )

        except KeyboardInterrupt:
            console.clear()
            continue
        except EOFError:
            exit_cli()


if __name__ == "__main__":
    main()

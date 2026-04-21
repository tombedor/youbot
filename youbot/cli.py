from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from youbot.app import YoubotApp
from youbot.controller import AppController


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="youbot")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("tui")
    subparsers.add_parser("scan")
    subparsers.add_parser("run-scheduled")

    add_repo = subparsers.add_parser("add-repo")
    add_repo.add_argument("path")
    add_repo.add_argument("--name", default=None)
    add_repo.add_argument("--classification", choices=["integrated", "managed"], default="integrated")

    init_managed = subparsers.add_parser("init-managed")
    init_managed.add_argument("path")
    init_managed.add_argument("--name", required=True)

    ask = subparsers.add_parser("ask")
    ask.add_argument("message")
    ask.add_argument("--repo", dest="repo_id", default=None)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command in (None, "tui"):
        YoubotApp().run()
        return

    if args.command == "scan":
        controller = AppController()
        payload = {
            "repos": [asdict(repo) for repo in controller.repos],
            "commands": {
                repo_id: [asdict(command) for command in commands]
                for repo_id, commands in controller.commands.items()
            },
        }
        print(json.dumps(payload, indent=2))
        return

    if args.command == "ask":
        controller = AppController()
        processed = controller.process_message(args.message, args.repo_id)
        print(processed.body)
        return

    if args.command == "run-scheduled":
        controller = AppController()
        results = controller.run_scheduled_jobs()
        payload = [
            {
                "repo_id": result.repo_id,
                "command_name": result.command_name,
                "exit_code": result.exit_code,
            }
            for result in results
        ]
        print(json.dumps(payload, indent=2))
        return

    if args.command == "add-repo":
        controller = AppController()
        repo = controller.register_repo(
            args.path,
            name=args.name,
            classification=args.classification,
        )
        print(
            json.dumps(
                {
                    "repo_id": repo.repo_id,
                    "name": repo.name,
                    "path": repo.path,
                    "classification": repo.classification,
                    "status": repo.status,
                    "adapter_id": repo.adapter_id,
                },
                indent=2,
            )
        )
        return

    if args.command == "init-managed":
        controller = AppController()
        print(controller.init_managed_repo(args.path, args.name))
        return

    parser.error(f"Unknown command: {args.command}")

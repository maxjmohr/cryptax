import sys

import inquirer


def main():
    questions = [
        inquirer.List(
            name="service",
            message="What service do you want to use?",
            choices=[
                "Print current returns",
                "Build visual dashboard",
                "Export tax report",
            ],
        )
    ]

    answer: dict | None = inquirer.prompt(questions)

    if answer is None:
        print("No function selected.")
        sys.exit()

    selected_service = answer["service"]
    print(f"You selected: {selected_service}")


if __name__ == "__main__":
    main()

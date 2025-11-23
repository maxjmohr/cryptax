import subprocess
import sys

import inquirer


def main():
    questions = [
        inquirer.List(
            name="service",
            message="What service do you want to use?",
            choices=[
                "Display portfolio standings in terminal",
                "Build visual dashboard using streamlit",
                "Export tax report as pdf",
            ],
        )
    ]

    answer: dict | None = inquirer.prompt(questions)

    if answer is None:
        print("No function selected.")
        sys.exit()

    selected_service = answer["service"]
    if selected_service == "Display portfolio standings in terminal":
        process = subprocess.Popen([sys.executable, "services/terminal/main.py"])
        process.wait()  # Wait until process ended

    else:
        print("Not implemented yet ;)")


if __name__ == "__main__":
    main()

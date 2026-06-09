import os
import re
import subprocess
import threading

from app import app, init_db

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

PORT = 5000
LOCAL_URL = f"http://127.0.0.1:{PORT}"


def start_cloudflared():
    cmd = ["cloudflared", "tunnel", "--url", LOCAL_URL]
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    printed = False

    for line in proc.stdout:
        match = re.search(r"https://[^\s]+\.trycloudflare\.com", line)
        if match and not printed:
            print(f"\n{GREEN}Public Link:{RESET} {match.group(0)}\n", flush=True)
            printed = True


def menu():
    while True:
        os.system("clear")
        print(f"""{CYAN}
╔══════════════════════════════╗
║      FORM SERVER MANAGER     ║
╚══════════════════════════════╝
{RESET}
{GREEN}[1]{RESET} Start Localhost
{GREEN}[2]{RESET} Start Public Link (Cloudflare)
{YELLOW}[3]{RESET} Dashboard URL
{RED}[4]{RESET} Exit
""")

        choice = input(f"{YELLOW}Choose Option: {RESET}").strip()

        if choice == "1":
            init_db()
            print(f"\n{GREEN}Starting Localhost...{RESET}\n", flush=True)
            app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False)

        elif choice == "2":
            init_db()
            print(f"\n{GREEN}Starting Public Link...{RESET}\n", flush=True)
            threading.Thread(target=start_cloudflared, daemon=True).start()
            app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False)

        elif choice == "3":
            print(f"\n{CYAN}Dashboard:{RESET}")
            print(f"{LOCAL_URL}/dashboard")
            input("\nPress Enter...")

        elif choice == "4":
            print(f"{RED}Goodbye!{RESET}")
            break

        else:
            print(f"{RED}Invalid option!{RESET}")
            input("Press Enter...")


if __name__ == "__main__":
    menu()

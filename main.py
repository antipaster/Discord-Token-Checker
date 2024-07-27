import threading
import requests
from colorama import Fore, Style
import os
import time

os.system("cls")
lc = f"{Fore.RESET}{Fore.LIGHTBLACK_EX}{Style.BRIGHT}[{Fore.LIGHTMAGENTA_EX}+{Style.BRIGHT}{Fore.LIGHTBLACK_EX}]{Fore.RESET}"
tokens = []
valid_tokens_count = 0
invalid_tokens_count = 0
nitro_count = 0
unclaimed_count = 0
mail_verified_count = 0
phone_verified_count = 0
full_verified_count = 0

results = []  # List to store results

def check_token_verification(token):
    global mail_verified_count, phone_verified_count, full_verified_count, unclaimed_count
    headers = {
        'Authorization': token
    }

    response = requests.get('https://discord.com/api/v10/users/@me', headers=headers)

    if response.status_code == 200:
        data = response.json()
        email_verification = data.get('verified', False)
        phone_verification = bool(data.get('phone'))

        if email_verification and phone_verification:
            full_verified_count += 1
            return "Full Verified"
        elif email_verification:
            mail_verified_count += 1
            return "Mail Verified"
        elif phone_verification:
            phone_verified_count += 1
            return "Phone Verified"
        else:
            unclaimed_count += 1
            return "Unclaimed"
    elif response.status_code == 401:
        return "invalid"
    else:
        return "error"

def check_boosts(token):
    headers = {
        'Authorization': token
    }

    response = requests.get('https://discord.com/api/v9/users/@me/guilds/premium/subscription-slots', headers=headers)
    if response.status_code == 200:
        data = response.json()
        if data:  # Check if data is not empty
            cooldown_count = sum(1 for entry in data if entry.get('cooldown_ends_at') is not None)
            boosts = 2 - int(cooldown_count)
            return boosts
        else:
            return 0
    else:
        return 0

def save_tokens_to_file(tokens, filename):
    with open(filename, "w", encoding="utf-8") as file:
        for token in tokens:
            file.write(f"{token}\n")

def check_token(token):
    global valid_tokens_count, invalid_tokens_count, nitro_count

    headers = {
        'Authorization': token
    }

    response = requests.get('https://discord.com/api/v9/users/@me', headers=headers)
    if response.status_code == 200:
        valid_tokens_count += 1
        user_data = response.json()
        premium_type = user_data.get('premium_type', 0)
        verification = check_token_verification(token)
        boosts = check_boosts(token)
        nitro = f"{Style.BRIGHT}{Fore.RED}NO_NITRO" if premium_type == 0 else f"{Style.BRIGHT}{Fore.GREEN}NITRO"
        if premium_type != 0:
            nitro_count += 1

        result = f"{token} | {verification}"
        results.append(result)

       # time.sleep(0.1)
        print(f'{lc} {Fore.LIGHTBLUE_EX}token={Fore.WHITE}{token[:20]}...{Fore.RESET} Flags: {Fore.RESET}{Fore.LIGHTBLACK_EX}{Style.BRIGHT}[{Fore.GREEN}VALID{Style.BRIGHT}{Fore.LIGHTBLACK_EX}]{Fore.RESET} {Fore.RESET}{Fore.LIGHTBLACK_EX}{Style.BRIGHT}[{Fore.BLUE}{boosts}_BOOSTS{Style.BRIGHT}{Fore.LIGHTBLACK_EX}]{Fore.RESET}, {Fore.RESET}{Fore.LIGHTBLACK_EX}{Style.BRIGHT}[{Fore.BLUE}{nitro}{Style.BRIGHT}{Fore.LIGHTBLACK_EX}]{Fore.RESET}, {Fore.RESET}{Fore.LIGHTBLACK_EX}{Style.BRIGHT}[{Fore.BLUE}{verification}{Style.BRIGHT}{Fore.LIGHTBLACK_EX}]{Fore.RESET} ')
        return token, verification, boosts, nitro
    elif response.status_code == 401:
        invalid_tokens_count += 1
        print(f'{lc} {Fore.LIGHTBLUE_EX}token={Fore.WHITE}{token[:20]}...{Fore.RESET} Flags: {Fore.RESET}{Fore.LIGHTBLACK_EX}{Style.BRIGHT}[{Fore.RED}INVALID{Style.BRIGHT}{Fore.LIGHTBLACK_EX}]{Fore.RESET}')
    elif response.status_code == 429:  # Rate limited
        retry_after = response.json().get("retry_after", 0)
        print(f'{lc} {Fore.LIGHTBLUE_EX}Token={Fore.WHITE}{token[:20]}...{Fore.RESET} is rate limited. Retrying after {retry_after} seconds...')
        time.sleep(retry_after)
        return check_token(token)
    else:
        print(f'{lc} {Fore.LIGHTBLUE_EX}token={Fore.WHITE}{token[:20]}...{Fore.RESET} Flags: {Fore.RESET}{Fore.LIGHTBLACK_EX}{Style.BRIGHT}[{Fore.RED}ERROR{Style.BRIGHT}{Fore.LIGHTBLACK_EX}]{Fore.RESET}')
    return None

def main():
    os.system("Title Token checker discord.gg/nekito")
    print(Fore.LIGHTMAGENTA_EX + '''
    discord.gg/nekito (fuck yo ascii)
    ''')
    with open("tokens.txt", "r") as file:
        tokens = file.readlines()

    tokens = [token.strip() for token in tokens]
    num_threads = 3
    total_tokens = len(tokens)
    tokens_per_thread = total_tokens // num_threads

    def check_tokens_worker(start, end):
        for i in range(start, end):
            token = tokens[i]
            result = check_token(token)
        
    threads = []
    for i in range(num_threads):
        start = i * tokens_per_thread
        end = (i + 1) * tokens_per_thread if i < num_threads - 1 else total_tokens
        thread = threading.Thread(target=check_tokens_worker, args=(start, end))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    # Save results to results.txt
    with open("results.txt", "w", encoding="utf-8") as file:
        for result in results:
            file.write(f"{result}\n")

    print(f"{lc}{Fore.GREEN} {'Valid Tokens: ' + str(valid_tokens_count) + f' {Fore.RESET}|{Fore.GREEN} ' if valid_tokens_count > 0 else ''}{f'{Fore.RED}Invalid Tokens: ' + str(invalid_tokens_count) + f' {Fore.RESET}|{Fore.GREEN} ' if invalid_tokens_count > 0 else ''}{'Nitro: ' + str(nitro_count) + f' {Fore.RESET}|{Fore.GREEN} ' if nitro_count > 0 else ''}{'Unclaimed: ' + str(unclaimed_count) + f' {Fore.RESET}|{Fore.GREEN} ' if unclaimed_count > 0 else ''}{'Mail Verified: ' + str(mail_verified_count) + f' {Fore.RESET}|{Fore.GREEN} ' if mail_verified_count > 0 else ''}{'Phone Verified: ' + str(phone_verified_count) + f' {Fore.RESET}|{Fore.GREEN} ' if phone_verified_count > 0 else ''}{'Full Verified: ' + str(full_verified_count) if full_verified_count > 0 else ''}")

main()
input("")

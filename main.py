import threading
import requests
from colorama import Fore, Style
import os
import time
import datetime

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

results = []  
BADGES = {
    1 << 0: "DISCORD_EMPLOYEE",
    1 << 1: "PARTNERED_SERVER_OWNER",
    1 << 2: "HYPESQUAD_EVENTS",
    1 << 3: "BUG_HUNTER_LEVEL_1",
    1 << 4: "HOUSE_BRAVERY",
    1 << 5: "HOUSE_BRILLIANCE",
    1 << 6: "HOUSE_BALANCE",
    1 << 7: "EARLY_SUPPORTER",
    1 << 8: "TEAM_USER",
    1 << 9: "BUG_HUNTER_LEVEL_2",
    1 << 10: "VERIFIED_BOT",
    1 << 11: "EARLY_VERIFIED_BOT_DEVELOPER",
    1 << 12: "DISCORD_CERTIFIED_MODERATOR",
    1 << 13: "DISCORD_PARTNER",
    1 << 14: "VERIFIED_DEVELOPER",

}



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

def extract_creation_year(user_id):
    # Discord IDs are Snowflakes; the first 42 bits are a timestamp in milliseconds since Discord Epoch (2015-01-01)
    discord_epoch = 1420070400000
    timestamp = (int(user_id) >> 22) + discord_epoch
    creation_date = datetime.datetime.utcfromtimestamp(timestamp / 1000)
    return creation_date.year

def get_badges(flags):
    badge_list = [name for value, name in BADGES.items() if flags & value]
    return ', '.join(badge_list) if badge_list else "No Badges"



def check_token(token):
    global valid_tokens_count, invalid_tokens_count, nitro_count

    headers = {
        'Authorization': token
    }

    response = requests.get('https://discord.com/api/v9/users/@me', headers=headers)
    if response.status_code == 200:
        valid_tokens_count += 1
        user_data = response.json()
        user_id = user_data['id']
        creation_year = extract_creation_year(user_id)
        premium_type = user_data.get('premium_type', 0)
        public_flags = user_data.get('public_flags', 0) 
        badges = get_badges(public_flags)
        verification = check_token_verification(token)
        boosts = check_boosts(token)
        nitro = "NITRO" if premium_type != 0 else "NO NITRO"
        if premium_type != 0:
            nitro_count += 1
        result = f"{token} | {verification} | Creation Year: {creation_year} | Nitro: {nitro} | Boosts: {boosts} | Badges: {badges}"
        results.append(result)

        print(f'{lc} {Fore.LIGHTBLUE_EX}token={Fore.WHITE}{token[:20]}...{Fore.RESET} Flags: {Fore.RESET}{Fore.LIGHTBLACK_EX}{Style.BRIGHT}[{Fore.GREEN}VALID{Style.BRIGHT}{Fore.LIGHTBLACK_EX}]{Fore.RESET} {Fore.RESET}{Fore.LIGHTBLACK_EX}{Style.BRIGHT}[{Fore.BLUE}{boosts}_BOOSTS{Style.BRIGHT}{Fore.LIGHTBLACK_EX}]{Fore.RESET}, {Fore.RESET}{Fore.LIGHTBLACK_EX}{Style.BRIGHT}[{Fore.BLUE}{nitro}{Style.BRIGHT}{Fore.LIGHTBLACK_EX}]{Fore.RESET}, {Fore.RESET}{Fore.LIGHTBLACK_EX}{Style.BRIGHT}[{Fore.BLUE}{verification}{Style.BRIGHT}{Fore.LIGHTBLACK_EX}]{Fore.RESET}, {Fore.RESET}{Fore.LIGHTBLACK_EX}{Style.BRIGHT}[{Fore.BLUE}Creation Year: {creation_year}{Style.BRIGHT}{Fore.LIGHTBLACK_EX}]{Fore.RESET}, {Fore.RESET}{Fore.LIGHTBLACK_EX}{Style.BRIGHT}[{Fore.BLUE}Badges: {badges}{Style.BRIGHT}{Fore.LIGHTBLACK_EX}]{Fore.RESET}')
        return token, verification, boosts, nitro, creation_year, badges
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

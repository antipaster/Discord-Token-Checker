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
billing_info_count = 0  

results = []
gifts = []  
promos = []  

proxies = []
use_proxies = False

def load_proxies():
    global proxies
    with open("proxies.txt", "r") as file:
        proxies = [line.strip() for line in file.readlines()]
        proxies = [f"http://{proxy}" if not proxy.startswith("http") else proxy for proxy in proxies]

def get_random_proxy():
    import random
    return random.choice(proxies) if proxies else None

def get_request_headers(token):
    return {'Authorization': token}

def get_request_proxies():
    if use_proxies:
        proxy = get_random_proxy()
        if proxy:
            return {
                'http': proxy,
                'https': proxy
            }
    return None

def check_token_verification(token):
    global mail_verified_count, phone_verified_count, full_verified_count, unclaimed_count
    headers = get_request_headers(token)
    proxy = get_request_proxies()

    response = requests.get('https://discord.com/api/v10/users/@me', headers=headers, proxies=proxy)

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
    headers = get_request_headers(token)
    proxy = get_request_proxies()

    response = requests.get('https://discord.com/api/v9/users/@me/guilds/premium/subscription-slots', headers=headers, proxies=proxy)
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

def check_billing_info(token):
    global billing_info_count
    headers = get_request_headers(token)
    proxy = get_request_proxies()

    response = requests.get('https://discord.com/api/v10/users/@me/billing/payment-sources', headers=headers, proxies=proxy)
    if response.status_code == 200:
        data = response.json()
        billing_info_count += len(data)
        return len(data)
    else:
        return 0

def check_gifts(token):
    headers = get_request_headers(token)
    proxy = get_request_proxies()

    response = requests.get('https://discord.com/api/v10/users/@me/entitlements/gift-codes', headers=headers, proxies=proxy)
    if response.status_code == 200:
        data = response.json()
        gift_codes = [gift['code'] for gift in data]
        gifts.extend(gift_codes)
        return gift_codes
    else:
        return []

def check_promos(token):
    headers = get_request_headers(token)
    proxy = get_request_proxies()

    response = requests.get('https://discord.com/api/v9/users/@me/outbound-promotions/codes?locale=fr', headers=headers, proxies=proxy)
    if response.status_code == 200:
        data = response.json()
        promo_codes = [promo['code'] for promo in data]
        promos.extend(promo_codes)
        return promo_codes
    else:
        return []

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

def check_token(token):
    global valid_tokens_count, invalid_tokens_count, nitro_count

    headers = get_request_headers(token)
    proxy = get_request_proxies()

    response = requests.get('https://discord.com/api/v9/users/@me', headers=headers, proxies=proxy)
    if response.status_code == 200:
        valid_tokens_count += 1
        user_data = response.json()
        user_id = user_data['id']
        creation_year = extract_creation_year(user_id)
        premium_type = user_data.get('premium_type', 0)
        public_flags = user_data.get('public_flags', 0) 
        verification = check_token_verification(token)
        boosts = check_boosts(token)
        billing_info = check_billing_info(token) 
        gift_codes = check_gifts(token)  
        promo_codes = check_promos(token)  
        nitro = "NITRO" if premium_type != 0 else "NO NITRO"
        if premium_type != 0:
            nitro_count += 1
        result = f"{token} | {verification} | Creation Year: {creation_year} | Nitro: {nitro} | Boosts: {boosts} | Billing Info: {billing_info} | Gifts: {len(gift_codes)} | Promos: {len(promo_codes)}"
        results.append(result)

        print(f'{lc} {Fore.LIGHTBLUE_EX}token={Fore.WHITE}{token[:20]}...{Fore.RESET} Flags: {Fore.RESET}{Fore.LIGHTBLACK_EX}{Style.BRIGHT}[{Fore.GREEN}VALID{Style.BRIGHT}{Fore.LIGHTBLACK_EX}]{Fore.RESET} {Fore.RESET}{Fore.LIGHTBLACK_EX}{Style.BRIGHT}[{Fore.BLUE}{boosts}_BOOSTS{Style.BRIGHT}{Fore.LIGHTBLACK_EX}]{Fore.RESET}, {Fore.RESET}{Fore.LIGHTBLACK_EX}{Style.BRIGHT}[{Fore.BLUE}{nitro}{Style.BRIGHT}{Fore.LIGHTBLACK_EX}]{Fore.RESET}, {Fore.RESET}{Fore.LIGHTBLACK_EX}{Style.BRIGHT}[{Fore.BLUE}{verification}{Style.BRIGHT}{Fore.LIGHTBLACK_EX}]{Fore.RESET}, {Fore.RESET}{Fore.LIGHTBLACK_EX}{Style.BRIGHT}[{Fore.BLUE}Creation Year: {creation_year}{Style.BRIGHT}{Fore.LIGHTBLACK_EX}]{Fore.RESET}, {Fore.RESET}{Fore.LIGHTBLACK_EX}{Style.BRIGHT}[{Fore.BLUE}Billing Info: {billing_info}{Style.BRIGHT}{Fore.LIGHTBLACK_EX}]{Fore.RESET}, {Fore.RESET}{Fore.LIGHTBLACK_EX}{Style.BRIGHT}[{Fore.BLUE}Gifts: {len(gift_codes)}{Style.BRIGHT}{Fore.LIGHTBLACK_EX}]{Fore.RESET}, {Fore.RESET}{Fore.LIGHTBLACK_EX}{Style.BRIGHT}[{Fore.BLUE}Promos: {len(promo_codes)}{Style.BRIGHT}{Fore.LIGHTBLACK_EX}]{Fore.RESET}')
        return token, verification, boosts, nitro, creation_year, billing_info, gift_codes, promo_codes
    elif response.status_code == 401:
        invalid_tokens_count += 1
        print(f'{lc} {Fore.LIGHTBLUE_EX}token={Fore.WHITE}{token[:20]}...{Fore.RESET} Flags: {Fore.RESET}{Fore.LIGHTBLACK_EX}{Style.BRIGHT}[{Fore.RED}INVALID{Style.BRIGHT}{Fore.LIGHTBLACK_EX}]{Fore.RESET}')
    elif response.status_code == 429:  # Rate limited
        retry_after = response.json().get("retry_after", 0)
        print(f'{lc} {Fore.LIGHTBLUE_EX}Token={Fore.WHITE}{token[:20]}...{Fore.RESET} is rate limited. Retrying after {retry_after} seconds...')
        time.sleep(retry_after)
        return check_token(token)
    else:
        print(f'{lc} {Fore.LIGHTBLUE_EX}token={Fore.WHITE}{token[:20]}...{Fore.RESET} Flags: {Fore.RESET}{Fore.LIGHTBLACK_EX}{Style.BRIGHT}[{Fore.YELLOW}ERROR{Style.BRIGHT}{Fore.LIGHTBLACK_EX}]{Fore.RESET}')
        return None

print(Fore.GREEN + '''
           /$$                                                   /$$                           /$$                
          |__/                                                  | $$                          | $$                
  /$$$$$$$ /$$  /$$$$$$  /$$$$$$/$$$$   /$$$$$$         /$$$$$$$| $$$$$$$   /$$$$$$   /$$$$$$$| $$   /$$  /$$$$$$ 
 /$$_____/| $$ /$$__  $$| $$_  $$_  $$ |____  $$       /$$_____/| $$__  $$ /$$__  $$ /$$_____/| $$  /$$/ |____  $$
|  $$$$$$ | $$| $$  \ $$| $$ \ $$ \ $$  /$$$$$$$      | $$      | $$  \ $$| $$$$$$$$| $$      | $$$$$$/   /$$$$$$$
 \____  $$| $$| $$  | $$| $$ | $$ | $$ /$$__  $$      | $$      | $$  | $$| $$_____/| $$      | $$_  $$  /$$__  $$
 /$$$$$$$/| $$|  $$$$$$$| $$ | $$ | $$|  $$$$$$$      |  $$$$$$$| $$  | $$|  $$$$$$$|  $$$$$$$| $$ \  $$|  $$$$$$$
|_______/ |__/ \____  $$|__/ |__/ |__/ \_______/       \_______/|__/  |__/ \_______/ \_______/|__/  \__/ \_______/
               /$$  \ $$                                                                                          
              |  $$$$$$/                                                                                          
               \______/                                                                                                                                                                  
    discord.gg/nekito 
    ''' + Fore.RESET)

use_proxies_input = input("Do you want to use proxies? (yes/no): ").strip().lower()
use_proxies = use_proxies_input == "yes"
num_threads = int(input("Threads: "))
if use_proxies:
    load_proxies()

with open("tokens.txt", "r") as file:
    tokens = file.readlines()

tokens = [token.strip() for token in tokens]

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


with open("results.txt", "w", encoding="utf-8") as file:
    for result in results:
        file.write(f"{result}\n")


with open("gifts.txt", "w", encoding="utf-8") as file:
    for gift in gifts:
        file.write(f"{gift}\n")


with open("promos.txt", "w", encoding="utf-8") as file:
    for promo in promos:
        file.write(f"{promo}\n")

print(f"{lc}{Fore.GREEN} {'Valid Tokens: ' + str(valid_tokens_count) + f' {Fore.RESET}|{Fore.GREEN} ' if valid_tokens_count > 0 else ''}{f'{Fore.RED}Invalid Tokens: ' + str(invalid_tokens_count) + f' {Fore.RESET}|{Fore.GREEN} ' if invalid_tokens_count > 0 else ''}{'Nitro: ' + str(nitro_count) + f' {Fore.RESET}|{Fore.GREEN} ' if nitro_count > 0 else ''}{'Unclaimed: ' + str(unclaimed_count) + f' {Fore.RESET}|{Fore.GREEN} ' if unclaimed_count > 0 else ''}{'Mail Verified: ' + str(mail_verified_count) + f' {Fore.RESET}|{Fore.GREEN} ' if mail_verified_count > 0 else ''}{'Phone Verified: ' + str(phone_verified_count) + f' {Fore.RESET}|{Fore.GREEN} ' if phone_verified_count > 0 else ''}{'Full Verified: ' + str(full_verified_count) + f' {Fore.RESET}|{Fore.GREEN} ' if full_verified_count > 0 else ''}{'Billing Info: ' + str(billing_info_count) if billing_info_count > 0 else ''}")

main()
input("")

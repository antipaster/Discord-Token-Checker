import threading
import requests
from colorama import Fore, Style
import os
import time
import datetime
from itertools import cycle
import json

# clear 
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
friend_count_total = 0
guilds_count_total = 0


results = []
gifts = [] 
promos = [] 

config = None

def load_config(filename='config.json'):
    global config
    with open(filename, 'r') as file:
        config = json.load(file)
    return config

def load_proxies(filename):
    with open(filename, "r") as file:
        proxy_lines = file.readlines()
    proxies = [line.strip() for line in proxy_lines if line.strip()]
    proxy_dict = {}
    for proxy in proxies:
        userpass, hostport = proxy.split('@')
        username, password = userpass.split(':')
        host, port = hostport.split(':')
        proxy_dict[proxy] = {
            "http": f"http://{username}:{password}@{host}:{port}",
            "https": f"http://{username}:{password}@{host}:{port}"  # hard coded
        }
    return proxy_dict

def get_proxy(proxies):
    if proxies:
        return next(proxies)
    return None

def check_token_verification(token, proxy=None):
    global mail_verified_count, phone_verified_count, full_verified_count, unclaimed_count
    headers = {
        'Authorization': token
    }
    try:
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
    except requests.RequestException as e:
        print(f"Error in check_token_verification: {e}")
        return "error"

def check_boosts(token, proxy=None):
    headers = {
        'Authorization': token
    }
    try:
        response = requests.get('https://discord.com/api/v9/users/@me/guilds/premium/subscription-slots', headers=headers, proxies=proxy)
        if response.status_code == 200:
            data = response.json()
            if data:
                cooldown_count = sum(1 for entry in data if entry.get('cooldown_ends_at') is not None)
                boosts = 2 - int(cooldown_count)
                return boosts
            else:
                return 0
        else:
            return 0
    except requests.RequestException as e:
        print(f"Error in check_boosts: {e}")
        return 0

def check_billing_info(token, proxy=None):
    headers = {
        'Authorization': token
    }

    try:
        response = requests.get('https://discord.com/api/v9/users/@me/billing/payment-sources', headers=headers, proxies=proxy)
        if response.status_code == 200:
            data = response.json()
            if not data:
                return []

            payment_methods = []
            for source in data:
                brand_type = source.get('type', None)
                if brand_type == 2:
                    brand = 'PayPal'
                elif brand_type == 7:
                    brand = 'PaySafeCard'
                else:
                    brand = source.get('brand', 'Unknown').title()

                invalid = source.get('invalid', False)
                payment_methods.append(f"{brand} {'Invalid' if invalid else 'Valid'}")
            return payment_methods
        return []
    except requests.RequestException as e:
        print(f"Error in check_billing_info: {e}")
        return []

def check_gifts(token, proxy=None):
    headers = {
        'Authorization': token
    }
    try:
        response = requests.get('https://discord.com/api/v9/users/@me/entitlements/gifts?country_code=PL', headers=headers, proxies=proxy)
        if response.status_code == 200:
            data = response.json()
            gift_details = []
            for gift in data:
                gift_code = gift.get('id')
                gift_style = gift.get('gift_style')
                sku = gift.get('sku', {})
                gift_name = sku.get('name', 'Unknown')

                if gift_code:
                    gift_details.append({
                        'code': gift_code,
                        'style': gift_style,
                        'name': gift_name
                    })

            gifts.extend(gift_details)
            return gift_details
        else:
            return []
    except requests.RequestException as e:
        print(f"Error in check_gifts: {e}")
        return []

def check_promos(token, proxy=None):
    headers = {
        'Authorization': token
    }
    try:
        response = requests.get('https://discord.com/api/v9/users/@me/outbound-promotions/codes?locale=fr', headers=headers, proxies=proxy)
        if response.status_code == 200:
            data = response.json()
            promo_details = [{
                'code': promo['code'],
                'name': promo['promotion']['outbound_title'],
                'claimed_at': promo.get('claimed_at', 'Unclaimed'),
                'end_date': promo['promotion']['outbound_redemption_end_date']
            } for promo in data]
            promos.extend(promo_details)
            return promo_details
        else:
            return []
    except requests.RequestException as e:
        print(f"Error in check_promos: {e}")
        return []

def check_guilds_count(token, proxy=None):
    headers = {
        'Authorization': token
    }
    try:
        response = requests.get('https://discord.com/api/v9/users/@me/guilds', headers=headers, proxies=proxy)
        if response.status_code == 200:
            data = response.json()
            return len(data)
        return 0
    except requests.RequestException as e:
        print(f"Error in check_guilds_count: {e}")
        return 0


def check_friends_count(token, proxy=None):
    headers = {
        'Authorization': token
    }
    try:
        response = requests.get('https://discord.com/api/v9/users/@me/relationships', headers=headers, proxies=proxy)
        if response.status_code == 200:
            data = response.json()
            friends_count = len([friend for friend in data if friend.get('type') == 1])
            return friends_count
        return 0
    except requests.RequestException as e:
        print(f"Error in check_friends_count: {e}")
        return 0

def save_gifts_to_file(gifts, filename):
    with open(filename, "w", encoding="utf-8") as file:
        for gift in gifts:
            file.write(f"Code: {gift['code']} | Style: {gift['style']} | Name: {gift['name']}\n")

def save_promos_to_file(promos, filename):
    with open(filename, "w", encoding="utf-8") as file:
        for promo in promos:
            file.write(f"{promo['code']} | {promo['name']} | {promo['claimed_at']} | {promo['end_date']}\n")

def calculate_score(user_data, config):
    score = 0
    current_year = datetime.datetime.utcnow().year

    if user_data.get('premium_type', 0) != 0:
        score += 50 


    if config['checks'].get('boosts', False):
        boosts = check_boosts(user_data['token'])
        score += boosts * 10

   
    if config['checks'].get('billing_info', False):
        billing_info = check_billing_info(user_data['token'])
        score += len(billing_info) * 5

  
    if config['checks'].get('gifts', False):
        gifts_count = len(check_gifts(user_data['token']))
        score += gifts_count * 5

   
    if config['checks'].get('promos', False):
        promos_count = len(check_promos(user_data['token']))
        score += promos_count * 5

    if config['checks'].get('friends_count', False):
        friends_count = check_friends_count(user_data['token'])
        score += friends_count * 2

    if config['checks'].get('guilds_count', False):
        guilds_count = check_guilds_count(user_data['token'])
        score += guilds_count * 2

 
    user_id = user_data.get('id')
    if user_id:
        creation_year = extract_creation_year(user_id)
        account_age = current_year - creation_year
        if account_age > 0:
            score += account_age * 3  

    return score

def save_tokens_to_file(tokens, filename):
    with open(filename, "w", encoding="utf-8") as file:
        for token in tokens:
            file.write(f"{token}\n")

def extract_creation_year(user_id):
    discord_epoch = 1420070400000
    timestamp = (int(user_id) >> 22) + discord_epoch
    creation_date = datetime.datetime.utcfromtimestamp(timestamp / 1000)
    return creation_date.year

def check_token(token, proxy=None, config=None):
    global valid_tokens_count, invalid_tokens_count, nitro_count, billing_info_count, friend_count_total, guilds_count_total

    headers = {
        'Authorization': token
    }

    try:
        response = requests.get('https://discord.com/api/v9/users/@me', headers=headers, proxies=proxy)
        if response.status_code == 200:
            valid_tokens_count += 1
            user_data = response.json()
            user_id = user_data['id']
            creation_year = extract_creation_year(user_id)
            premium_type = user_data.get('premium_type', 0)
            public_flags = user_data.get('public_flags', 0)
            user_data['token'] = token
            score = calculate_score(user_data, config)
            config = load_config()  

            verification = check_token_verification(token, proxy) if config['checks'].get('verification', False) else "Not Checked"
            boosts = check_boosts(token, proxy) if config['checks'].get('boosts', False) else "Not Checked"
            payment_methods = check_billing_info(token, proxy) if config['checks'].get('billing_info', False) else []
            billing_info_display = len(payment_methods) if config['checks'].get('billing_info', False) else 0
            gift_codes = check_gifts(token, proxy) if config['checks'].get('gifts', False) else []
            promo_codes = check_promos(token, proxy) if config['checks'].get('promos', False) else []
            friends_count = check_friends_count(token, proxy) if config['checks'].get('friends_count', False) else 0
            guilds_count = check_guilds_count(token, proxy) if config['checks'].get('guilds_count', False) else 0

            nitro = "NITRO" if premium_type != 0 else "NO NITRO"
            if premium_type != 0:
                nitro_count += 1

            flags = ""
            flags += f"Verification: {verification} | " if config['checks'].get('verification', False) else ""
            flags += f"Boosts: {boosts} | " if config['checks'].get('boosts', False) else ""
            flags += f"Nitro: {nitro} | " if config['checks'].get('nitro', False) else ""
            flags += f"Creation Year: {creation_year} | " if config['checks'].get('creation_year', False) else ""
            flags += f"Billing Info: {billing_info_display} ({', '.join(payment_methods) if payment_methods else 'None'}) | " if config['checks'].get('billing_info', False) else ""
            flags += f"Gifts: {len(gift_codes)} | " if config['checks'].get('gifts', False) else ""
            flags += f"Promos: {len(promo_codes)} | " if config['checks'].get('promos', False) else ""
            flags += f"Friends Count: {friends_count} | " if config['checks'].get('friends_count', False) else ""
            flags += f"Guilds Count: {guilds_count}" if config['checks'].get('guilds_count', False) else ""

           # lock check (@ekkoreerandom)
            billing_response = requests.get('https://canary.discord.com/api/v9/users/@me/billing/payment-sources', headers=headers, proxies=proxy)
            if billing_response.status_code == 403:
                print(f'{lc} {Fore.LIGHTBLUE_EX}token={Fore.WHITE}{token[:20]}...{Fore.RESET} Flags: {Fore.RESET}{Fore.LIGHTBLACK_EX}{Style.BRIGHT}'
                      f'[{Fore.YELLOW}LOCKED{Style.BRIGHT}{Fore.LIGHTBLACK_EX}]{Fore.RESET}')
                return token, "Locked"

            results.append((token, flags, score))
            print(f'{lc} {Fore.LIGHTBLUE_EX}token={Fore.WHITE}{token[:20]}...{Fore.RESET} Flags: {Fore.RESET}{Fore.LIGHTBLACK_EX}{Style.BRIGHT}'
                  f'[{Fore.GREEN}VALID{Style.BRIGHT}{Fore.LIGHTBLACK_EX}]{Fore.RESET} {flags}')
            return token, flags

        elif response.status_code == 401:
            invalid_tokens_count += 1
            print(f'{lc} {Fore.LIGHTBLUE_EX}token={Fore.WHITE}{token[:20]}...{Fore.RESET} Flags: {Fore.RESET}{Fore.LIGHTBLACK_EX}{Style.BRIGHT}'
                  f'[{Fore.RED}INVALID{Style.BRIGHT}{Fore.LIGHTBLACK_EX}]{Fore.RESET}')
            return token, "Invalid"
        elif response.status_code == 429:  # Rate limited
            retry_after = response.json().get("retry_after", 0)
            print(f'{lc} {Fore.LIGHTBLUE_EX}Token={Fore.WHITE}{token[:20]}...{Fore.RESET} is rate limited. Retrying after {retry_after} seconds...')
            time.sleep(retry_after)
            return check_token(token, proxy)
        else:
            print(f'{lc} {Fore.LIGHTBLUE_EX}token={Fore.WHITE}{token[:20]}...{Fore.RESET} Flags: {Fore.RESET}{Fore.LIGHTBLACK_EX}{Style.BRIGHT}'
                  f'[{Fore.RED}ERROR{Style.BRIGHT}{Fore.LIGHTBLACK_EX}]{Fore.RESET}')
            return token, "Error"
    except requests.RequestException as e:
        print(f"Error in check_token: {e}")
    return token, "Error"


def sort_results(results, sort_by_worth):
    if sort_by_worth:
        return sorted(results, key=lambda x: x[2], reverse=True)
    return results



def main():
    global config
    os.system("Title Token checker discord.gg/nekito")
    print(Fore.LIGHTMAGENTA_EX + '''
 
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

    config = load_config() 

    sort_by_worth = config.get('sort_by_worth', False)

    with open("tokens.txt", "r", encoding="utf-8") as file:
        tokens = file.readlines()


    tokens = list(set(token.strip() for token in tokens))
    total_tokens = len(tokens)
    num_threads = int(input("Threads: "))
    sleep_num = int(input("Sleep time for threads: "))
    tokens_per_thread = total_tokens // num_threads

    def check_tokens_worker(start, end):
        for i in range(start, end):
            token = tokens[i]
            result = check_token(token, config=config) 
            time.sleep(sleep_num)

    threads = []
    for i in range(num_threads):
        start = i * tokens_per_thread
        end = (i + 1) * tokens_per_thread if i < num_threads - 1 else total_tokens
        thread = threading.Thread(target=check_tokens_worker, args=(start, end))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    results_sorted = sort_results(results, sort_by_worth)

    with open("results.txt", "w", encoding="utf-8") as file:
        for token, flags, _ in results_sorted:
            file.write(f"{token} | {flags}\n")

    save_gifts_to_file(gifts, "gifts.txt")
    save_promos_to_file(promos, "promos.txt")

    print(f"{lc}{Fore.GREEN} {'Tokens: ' + str(valid_tokens_count) + f' {Fore.RESET}|{Fore.GREEN} ' if valid_tokens_count > 0 else ''}{f'{Fore.RED}Invalid Tokens: ' + str(invalid_tokens_count) + f' {Fore.RESET}|{Fore.GREEN} ' if invalid_tokens_count > 0 else ''}{'Nitro: ' + str(nitro_count) + f' {Fore.RESET}|{Fore.GREEN} ' if nitro_count > 0 else ''}{'Unclaimed: ' + str(unclaimed_count) + f' {Fore.RESET}|{Fore.GREEN} ' if unclaimed_count > 0 else ''}{'Mail Verified: ' + str(mail_verified_count) + f' {Fore.RESET}|{Fore.GREEN} ' if mail_verified_count > 0 else ''}{'Phone Verified: ' + str(phone_verified_count) + f' {Fore.RESET}|{Fore.GREEN} ' if phone_verified_count > 0 else ''}{'Full Verified: ' + str(full_verified_count) + f' {Fore.RESET}|{Fore.GREEN} ' if full_verified_count > 0 else ''}{'Billing Info: ' + str(billing_info_count) if billing_info_count > 0 else ''}{'Friends Count: ' + str(friend_count_total) if friend_count_total > 0 else ''}{'Guilds Count: ' + str(guilds_count_total) if guilds_count_total > 0 else ''}")

main()
input("")


import threading
import requests
from colorama import Fore, Style
import os
import time
import datetime
from itertools import cycle

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
            "https": f"http://{username}:{password}@{host}:{port}"  # hard codded 
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
def check_billing_info(token, proxy):
    headers = {
        'Authorization': token
    }

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
            elif  brand_type == 7:
                brand = 'PaySafeCard'
            else:
                brand = source.get('brand', 'Unknown').title()

            invalid = source.get('invalid', False)
            payment_methods.append(f"{brand} {'Invalid' if invalid else 'Valid'}")
        return payment_methods
    return [] 


def save_gifts_to_file(gifts, filename):
    with open(filename, "w", encoding="utf-8") as file:
        for gift in gifts:
            file.write(f"Code: {gift['code']} | Style: {gift['style']} | Name: {gift['name']}\n")


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
                gift_code = gift.get('id')  #
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


def save_promos_to_file(promos, filename):
    with open(filename, "w", encoding="utf-8") as file:
        for promo in promos:
            file.write(f"{promo['code']} | {promo['name']} | {promo['claimed_at']} | {promo['end_date']}\n")

       

def save_tokens_to_file(tokens, filename):
    with open(filename, "w", encoding="utf-8") as file:
        for token in tokens:
            file.write(f"{token}\n")

def extract_creation_year(user_id):
    discord_epoch = 1420070400000
    timestamp = (int(user_id) >> 22) + discord_epoch
    creation_date = datetime.datetime.utcfromtimestamp(timestamp / 1000)
    return creation_date.year

def check_token(token, proxies=None):
    global valid_tokens_count, invalid_tokens_count, nitro_count, billing_info_count

    proxy = get_proxy(proxies)
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
            verification = check_token_verification(token, proxy)
            boosts = check_boosts(token, proxy)
            payment_methods = check_billing_info(token, proxy)
            billing_info_count = len(payment_methods)  # ekkoree iq count (max 1)
            billing_info_display = billing_info_count if billing_info_count > 0 else 0
            gift_codes = check_gifts(token, proxy)
            promo_codes = check_promos(token, proxy)
            nitro = "NITRO" if premium_type != 0 else "NO NITRO"
            if premium_type != 0:
                nitro_count += 1

            result = (f"{token} | {verification} | Creation Year: {creation_year} | Nitro: {nitro} | Boosts: {boosts} | "
                      f"Billing Info: {billing_info_display} ({', '.join(payment_methods) if payment_methods else 'None'}) | Gifts: {len(gift_codes)} | Promos: {len(promo_codes)}")
            results.append(result)

            print(f'{lc} {Fore.LIGHTBLUE_EX}token={Fore.WHITE}{token[:20]}...{Fore.RESET} Flags: {Fore.RESET}{Fore.LIGHTBLACK_EX}{Style.BRIGHT}'
                  f'[{Fore.GREEN}VALID{Style.BRIGHT}{Fore.LIGHTBLACK_EX}]{Fore.RESET} {Fore.RESET}{Fore.LIGHTBLACK_EX}{Style.BRIGHT}'
                  f'[{Fore.BLUE}{boosts}_BOOSTS{Style.BRIGHT}{Fore.LIGHTBLACK_EX}]{Fore.RESET}, {Fore.RESET}{Fore.LIGHTBLACK_EX}{Style.BRIGHT}'
                  f'[{Fore.BLUE}{nitro}{Style.BRIGHT}{Fore.LIGHTBLACK_EX}]{Fore.RESET}, {Fore.RESET}{Fore.LIGHTBLACK_EX}{Style.BRIGHT}'
                  f'[{Fore.BLUE}{verification}{Style.BRIGHT}{Fore.LIGHTBLACK_EX}]{Fore.RESET}, {Fore.RESET}{Fore.LIGHTBLACK_EX}{Style.BRIGHT}'
                  f'[{Fore.BLUE}Creation Year: {creation_year}{Style.BRIGHT}{Fore.LIGHTBLACK_EX}]{Fore.RESET}, {Fore.RESET}{Fore.LIGHTBLACK_EX}{Style.BRIGHT}'
                  f'[{Fore.BLUE}Billing Info: {billing_info_display} ({", ".join(payment_methods) if payment_methods else "None"}){Style.BRIGHT}{Fore.LIGHTBLACK_EX}]{Fore.RESET}, {Fore.RESET}'
                  f'{Fore.LIGHTBLACK_EX}{Style.BRIGHT}[{Fore.BLUE}Gifts: {len(gift_codes)}{Style.BRIGHT}{Fore.LIGHTBLACK_EX}]{Fore.RESET}, {Fore.RESET}{Fore.LIGHTBLACK_EX}'
                  f'{Style.BRIGHT}[{Fore.BLUE}Promos: {len(promo_codes)}{Style.BRIGHT}{Fore.LIGHTBLACK_EX}]{Fore.RESET}')
            return token, verification, boosts, nitro, creation_year, billing_info_display, gift_codes, promo_codes
        elif response.status_code == 401:
            invalid_tokens_count += 1
            print(f'{lc} {Fore.LIGHTBLUE_EX}token={Fore.WHITE}{token[:20]}...{Fore.RESET} Flags: {Fore.RESET}{Fore.LIGHTBLACK_EX}{Style.BRIGHT}'
                  f'[{Fore.RED}INVALID{Style.BRIGHT}{Fore.LIGHTBLACK_EX}]{Fore.RESET}')
        elif response.status_code == 429:  # Rate limited
            retry_after = response.json().get("retry_after", 0)
            print(f'{lc} {Fore.LIGHTBLUE_EX}Token={Fore.WHITE}{token[:20]}...{Fore.RESET} is rate limited. Retrying after {retry_after} seconds...')
            time.sleep(retry_after)
            return check_token(token, proxies)
        else:
            print(f'{lc} {Fore.LIGHTBLUE_EX}token={Fore.WHITE}{token[:20]}...{Fore.RESET} Flags: {Fore.RESET}{Fore.LIGHTBLACK_EX}{Style.BRIGHT}'
                  f'[{Fore.RED}ERROR{Style.BRIGHT}{Fore.LIGHTBLACK_EX}]{Fore.RESET}')
    except requests.RequestException as e:
        print(f"Error in check_token: {e}")
    return None




def main():
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

    use_proxies = input("Do you want to use proxies? (y/n): ").strip().lower() == 'y'
    time_till_check = float(input("Thread Sleep time: "))
    if use_proxies:
        proxies = load_proxies("proxies.txt")
        proxy_pool = cycle(proxies.values())
    else:
        proxy_pool = None

    with open("tokens.txt", "r") as file:
        tokens = file.readlines()

    tokens = [token.strip() for token in tokens]
    num_threads = int(input("Threads: "))
    total_tokens = len(tokens)
    tokens_per_thread = total_tokens // num_threads

    def check_tokens_worker(start, end):
        for i in range(start, end):
            token = tokens[i]
            result = check_token(token, proxy_pool)
            time.sleep(time_till_check)
        
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
            
    save_gifts_to_file(gifts, "gifts.txt")
    save_promos_to_file(promos, "promos.txt")

    print(f"{lc}{Fore.GREEN} {'Valid Tokens: ' + str(valid_tokens_count) + f' {Fore.RESET}|{Fore.GREEN} ' if valid_tokens_count > 0 else ''}{f'{Fore.RED}Invalid Tokens: ' + str(invalid_tokens_count) + f' {Fore.RESET}|{Fore.GREEN} ' if invalid_tokens_count > 0 else ''}{'Nitro: ' + str(nitro_count) + f' {Fore.RESET}|{Fore.GREEN} ' if nitro_count > 0 else ''}{'Unclaimed: ' + str(unclaimed_count) + f' {Fore.RESET}|{Fore.GREEN} ' if unclaimed_count > 0 else ''}{'Mail Verified: ' + str(mail_verified_count) + f' {Fore.RESET}|{Fore.GREEN} ' if mail_verified_count > 0 else ''}{'Phone Verified: ' + str(phone_verified_count) + f' {Fore.RESET}|{Fore.GREEN} ' if phone_verified_count > 0 else ''}{'Full Verified: ' + str(full_verified_count) + f' {Fore.RESET}|{Fore.GREEN} ' if full_verified_count > 0 else ''}{'Billing Info: ' + str(billing_info_count) if billing_info_count > 0 else ''}")

main()
input("")

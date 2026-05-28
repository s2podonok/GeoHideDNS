import os
import sys
import requests
import time

def fetch_hosts(urls):
    domains = {}
    for url in urls:
        if not url or not url.strip():
            continue
        try:
            print(f"Загружаю {url}")
            resp = requests.get(url.strip(), timeout=10)
            if resp.status_code == 200:
                for line in resp.text.splitlines():
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    parts = line.split()
                    if len(parts) >= 2:
                        ip, domain = parts[0], parts[1]
                        is_block = ip in ('0.0.0.0', '127.0.0.1')
                        if domain not in domains:
                            domains[domain] = is_block
                print(f"  Найдено записей: {len([l for l in resp.text.splitlines() if l.strip() and not l.startswith('#')])}")
            else:
                print(f"  Ошибка: HTTP {resp.status_code}")
        except Exception as e:
            print(f"  Ошибка: {e}")
    return domains

def update_nextdns(domains, auth_secret, client_id):
    headers = {'X-Api-Key': auth_secret, 'Content-Type': 'application/json'}
    base_url = f'https://api.nextdns.io/profiles/{client_id}'
    
    count = 0
    for domain, is_block in domains.items():
        if is_block:
            url = f'{base_url}/denylist'
            data = {'id': domain, 'active': True}
        else:
            url = f'{base_url}/rewrites'
            data = {'domain': domain, 'ip': '45.90.28.0'}
        
        try:
            resp = requests.post(url, headers=headers, json=data)
            if resp.status_code in (200, 201):
                count += 1
                if count % 50 == 0:
                    print(f"  Прогресс: {count} доменов обработано")
            else:
                print(f"  Ошибка {domain}: {resp.status_code}")
            time.sleep(0.5)
        except Exception as e:
            print(f"  Ошибка API: {e}")
    print(f"Готово! Обработано {count} доменов")

print("=== Запуск обновления DNS ===")
print(f"Провайдер: {os.environ.get('DNS_PROVIDER', 'не задан')}")

provider = os.environ.get('DNS_PROVIDER', '').lower()
auth = os.environ.get('AUTH_SECRET')
client = os.environ.get('CLIENT_ID')

if not auth or not client:
    print('Ошибка: AUTH_SECRET или CLIENT_ID не заданы')
    sys.exit(1)

redirect_urls = os.environ.get('REDIRECT_URLS', '').split(',')
all_urls = [u.strip() for u in redirect_urls if u.strip()]

if not all_urls:
    print('Ошибка: нет URL для загрузки')
    sys.exit(1)

print(f"URL для загрузки: {all_urls}")
domains = fetch_hosts(all_urls)
print(f"Получено {len(domains)} уникальных доменов")

if provider == 'nextdns':
    update_nextdns(domains, auth, client)
else:
    print(f'Неподдерживаемый провайдер: {provider}')
    sys.exit(1)

print("=== Обновление завершено ===")

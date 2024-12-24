import cloudscraper
from eth_account import Account
from eth_account.messages import encode_defunct
from datetime import datetime, timezone

# URL'ы
nonce_url = "https://app.dynamicauth.com/api/v0/sdk/4cb32f63-9b0d-443e-92b6-5d4582fb626e/nonce"
verify_url = "https://app.dynamicauth.com/api/v0/sdk/4cb32f63-9b0d-443e-92b6-5d4582fb626e/verify"

with open('private.txt') as file:
    private_key = file.read().splitlines()
with open('proxy.txt') as file:
    proxies = file.read().splitlines()

for i in range(len(private_key)):
    proxy = {
        'http': f'http://{proxies[i]}',
        'https': f'http://{proxies[i]}'
    }
    public_wallet_address = Account.from_key(private_key[i]).address

    scraper = cloudscraper.create_scraper()
    nonce_response = scraper.get(nonce_url, proxies=proxy)     # Получаем нонс

    if nonce_response.status_code != 200:
        print("Ошибка получения нонса:", nonce_response.status_code, nonce_response.text)

    nonce = nonce_response.json().get("nonce")
    if not nonce:
        print("Ошибка: нонс отсутствует в ответе", nonce_response.text)

    issued_at = datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace("+00:00", "Z")

    message_to_sign = f"""app.gte.xyz wants you to sign in with your Ethereum account:
    {public_wallet_address}
    
    Sign this message to join the GTE waitlist. Signing this message does not give us permissions to access your balance or any other information, it is strictly for the purpose of joining the waitlist.
    
    URI: https://app.gte.xyz/
    Version: 1
    Chain ID: 1
    Nonce: {nonce}
    Issued At: {issued_at}
    Request ID: 4cb32f63-9b0d-443e-92b6-5d4582fb626e"""

    encoded_message = encode_defunct(text=message_to_sign)

    signed_message = Account.sign_message(encoded_message, private_key[i])

    # Формируем payload
    payload = {
        "signedMessage": '0x' + signed_message.signature.hex(),
        "messageToSign": message_to_sign,
        "publicWalletAddress": public_wallet_address,
        "chain": "EVM",
        "walletName": "rabby",
        "walletProvider": "browserExtension",
        "network": "1",
        "additionalWalletAddresses": []
    }

    # Отправляем запрос на сервер
    response = scraper.post(verify_url, json=payload, proxies=proxy)

    # Выводим результат
    print(f"{i}. {public_wallet_address} | Sign in enabled: {response.json()['user']['verifiedCredentials'][0]['signInEnabled']}")

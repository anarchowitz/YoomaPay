import requests


user_id = '123123'
parameters = {
    "token": "30283:AAAtUrEajzoZQX0iYjC58NJtTbfL520Q0Us",
    "api_url": "https://testnet-pay.crypt.bot/"
}
#для наглядности

class CryptoPay(object):
    def __init__(self, user_id, parameters) -> None:
        self.token = parameters['token']
        self.api_url = parameters['api_url']
        self.user_id = user_id
        self.headers = {
            "Crypto-Pay-API-Token": self.token
        }
        pass


    def get_me(self):
        getMe_url = f"{self.api_url}api/getMe"
        try:
            app_info = requests.get(getMe_url, headers = self.headers).json()
            return app_info
        except:
            return False
    def create_invoice(self, amount, asset='TON', description=None, hidden_message='Оплата прошла успешно!', expires_in=86400, allow_anonymous=False, allow_comments=False):
        payload = self.user_id
        invoice_url = f"{self.api_url}api/createInvoice"
        params = {
            "asset": asset,
            "amount": amount,
            "payload": payload,
            "hidden_message": hidden_message,
            "expires_in": expires_in,
            "allow_anonymous": allow_anonymous,
            "allow_comments": allow_comments
        }
        if description:
            params["description"] = description
        try:
            invoice_info = requests.get(invoice_url, headers=self.headers, params=params).json()
            return invoice_info
        except:
            return False
    def get_all_invoices(self):
        invoices_url = f"{self.api_url}api/getInvoices"
        invoice_info = requests.get(invoices_url, headers = self.headers).json()
        return invoice_info
        return False
    def get_invoice(self, invoice_id):
        invoices_list = self.get_all_invoices()
        if invoices_list:
            return [invoice for invoice in invoices_list["result"]["items"] if invoice["invoice_id"] == invoice_id]
        else:
            return False

cryptopay = CryptoPay(user_id, parameters)
invoice_info = cryptopay.create_invoice(amount=0.037, asset='DOGE')
pay_url = invoice_info['result']['pay_url']
# 'allowed_crypto_assets': ['USDT', 'TON', 'BTC', 'DOGE', 'LTC', 'ETH', 'BNB', 'TRX', 'USDC', 'JET', 'SEND']}}
print(invoice_info)
print('\n', pay_url)
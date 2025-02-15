from aiocryptopay import AioCryptoPay, Networks
import asyncio

token = "340700:AAmEHzF9g2gXFP2p7N3hP1tiR689jFv0H5s"

crypto = AioCryptoPay(token=token, network=Networks.MAIN_NET)

async def new_invoice():
    # Get supported assets
    supported_assets = await crypto.get_currencies()
    print("Supported assets:", supported_assets)

    # Check if 'USDT' is supported
    if 'USDT' in supported_assets:
        invoice = await crypto.create_invoice(asset='USDT', amount=1.5, allow_anonymous=False, allow_comments=False, hidden_message="Техническая поддержка: @anarchowitz")
        pay_url = invoice.bot_invoice_url
        invoice_id = invoice.invoice_id
        print(await crypto.get_invoices(invoice_id))
        print(invoice, pay_url, invoice_id, sep="\n\n")
    else:
        print("Asset 'USDT' is not supported. Please use a different asset.")

asyncio.run(new_invoice())
print(crypto.get_exchange_rates())
import asyncio, logging, re, requests
from datetime import datetime

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, Message, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, PreCheckoutQuery
from aiogram.types.message import ContentType
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from aiocryptopay import AioCryptoPay, Networks, exceptions
from database import conn, cursor


class Form(StatesGroup):
    crypto = State()
    crypto_amount = State()
    stars = State()
    profile = State()

token = "7939037867:AAHhuUFYN0nSkbf2ktN4a2c-Ab-R2dVg5-A"
cryptobot_token = "30355:AAhrsWWLEgNzbHVzUlCwTTuA2bFmwIy71Jj"
admin_id_list =  ['1177915114', '947603836']
crypto = AioCryptoPay(token=cryptobot_token, network=Networks.TEST_NET)
logging.basicConfig(level=logging.INFO)
bot = Bot(token=token)
dp = Dispatcher()


# Хэндлер на команду /start
@dp.message(Command("paysupport"))
async def pay_support_handler(message: types.Message):  
    await message.answer(  
        text="Добровольные пожертвования не подразумевают возврат средств, "  
        "однако, если вы очень хотите вернуть средства - свяжитесь с нами.")
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    telegram_id = message.from_user.id
    cursor.execute("SELECT join_date FROM profiles WHERE telegram_id = ?", (telegram_id,))
    join_date = cursor.fetchone()
    if not join_date:
        cursor.execute("INSERT INTO profiles (id, telegram_id, join_date) VALUES (NULL, ?, ?)", (telegram_id, message.date))
        conn.commit()
    else:
        pass
    
    mainbutton = [
        [types.KeyboardButton(text="💵Пополнить баланс")],
        [types.KeyboardButton(text="🆘Связь с поддержкой")],
        [types.KeyboardButton(text="👤Мой профиль")]
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=mainbutton,
        resize_keyboard=True,
        input_field_placeholder="Выберите нужный пункт в меню"
    )
    await message.answer("👋 Привет! Я помогу тебе с пополнением баланса на yooma.su.\nПользуясь ботом ты соглашаешься с пользовательским соглашением", reply_markup=keyboard)
#обработка нажатий кнопок
@dp.message(F.text == "💵Пополнить баланс")
async def echo(message: types.Message):
    telegram_id = message.from_user.id
    cursor.execute("SELECT profile_url FROM profiles WHERE telegram_id = ?", (telegram_id,))
    profile_url = cursor.fetchone()
    if profile_url and profile_url[0]:
        inline_kb_list = [
            [
                InlineKeyboardButton(text="⭐️ 1) Пополнить звездами (TG Stars)", callback_data='starsmethod_payment'),
            ],  
            [   
                InlineKeyboardButton(text="💸 2) Пополнить криптовалютой (CryptoBot)", callback_data='cryptomethod_payment'),
            ],  
            [
                InlineKeyboardButton(text="📊 3) Курс пополнений", callback_data='deposit_rate')
            ]
        ]
        await message.answer("Выберите способ пополнения баланса.", ignore_case=True, reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_kb_list))
    else:
        await message.answer('Чтобы пополнить баланс, сначала укажите свой профиль, на который будут начисляться средства. Для этого просто нажмите на кнопку "Мой профиль"', ignore_case=True)

@dp.callback_query(F.data == 'deposit_rate')
async def deposit_rate(callback: types.CallbackQuery):
    await callback.answer()
    rates = get_crypto_rates()
    rates['Звезда'] = 1.3  # добавляем курс "Звезды"
    message_text = "📊 Курс валют:\n\n"
    # Сначала выводим курс "Звезды"
    message_text += f"1 Звезда = {rates['Звезда']} RUB\n\n"
    # Затем выводим остальные курсы
    for currency, rate in rates.items():
        if currency != 'Звезда':
            # Преобразуем значение float в int
            rate_int = int(rate)
            message_text += f"1 {currency} = {rate_int} RUB\n"
    await callback.message.answer(message_text)
    await callback.message.answer('\nСовет: звезды дешевле всего можно купить в https://fragment.com/stars/buy')

@dp.callback_query(F.data == 'cryptomethod_payment')
async def cryptomethod_payment(callback: types.CallbackQuery, state: FSMContext):
    inline_kb_list = [
        [
            InlineKeyboardButton(text="USDT", callback_data='USDT'),
            InlineKeyboardButton(text="TON", callback_data='TON'),
            InlineKeyboardButton(text="BTC", callback_data='BTC'),
        ],
        [
            InlineKeyboardButton(text="DOGE", callback_data='DOGE'),
            InlineKeyboardButton(text="LTC", callback_data='LTC'),
            InlineKeyboardButton(text="ETH", callback_data='ETH'),
        ],
        [
            InlineKeyboardButton(text="BNB", callback_data='BNB'),
            InlineKeyboardButton(text="TRX", callback_data='TRX'),
            InlineKeyboardButton(text="USDC", callback_data='USDC'),
        ]
    ]
    await callback.message.answer("В какой валюте хотите оплатить?", reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_kb_list))
    await callback.answer()
    await state.set_state(Form.crypto)

@dp.callback_query(F.data.in_(['USDT', 'TON', 'BTC', 'DOGE', 'LTC', 'ETH', 'BNB', 'TRX', 'USDC']))
async def crypto_currency(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Сколько валюты хотите потратить?")
    await state.update_data(crypto_currency=callback.data)
    await state.set_state(Form.crypto_amount)

@dp.message(Form.crypto_amount, F.text.regexp(r'^\d+(\.\d+)?$'))
async def crypto_amount(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    cursor.execute("SELECT profile_url FROM profiles WHERE telegram_id = ?", (telegram_id,))
    profile_url = cursor.fetchone()
    if profile_url and profile_url[0]:
        try:
            insert_price = float(message.text)
            data = await state.get_data()
            crypto_currency = data.get('crypto_currency')
            invoice = await crypto.create_invoice(asset=crypto_currency, amount=insert_price, allow_anonymous=False, allow_comments=False, hidden_message="Техническая поддержка: @anarchowitz")
            pay_url = invoice.bot_invoice_url
            invoice_id = invoice.invoice_id
            inline_kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="Проверить оплату", callback_data="cryptocheck_payments")]
                ]
            )
            await message.answer(f"Сумма пополнения: {insert_price} {crypto_currency}\nСсылка для пополнения: \n{pay_url}", reply_markup=inline_kb)
            await state.update_data(invoice_id=invoice_id, insert_price=insert_price)  # сохраняем insert_price в состоянии
        except ValueError:
            await message.answer("Пожалуйста, введите сумму для пополнения баланса.")
    else:
        await message.answer('Чтобы пополнить баланс, сначала укажите свой профиль, на который будут начисляться средства. Для этого просто нажмите на кнопку "Мой профиль"', ignore_case=True)
@dp.callback_query(F.data == 'cryptocheck_payments')
async def cryptocheck_payments(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    invoice_id = data.get('invoice_id')
    insert_price = data.get('insert_price')
    crypto_currency = data.get('crypto_currency')
    telegram_id = callback.from_user.id
    cursor.execute("SELECT profile_url FROM profiles WHERE telegram_id = ?", (telegram_id,))
    profile_url = cursor.fetchone()
    status = await get_invoice(invoice_id)
    if status == 'paid':
        await callback.message.reply("Оплата прошла успешно!")
        await bot.send_message(callback.message.cxhat.id, "Ваш заказ на выдачу баланса был отправлен. Ожидайте в течение суток.")
        crypto_rates = get_crypto_rates()
        rub_amount = insert_price * crypto_rates[crypto_currency]
        for i in range(0, len(admin_id_list)):
            admin_id = admin_id_list[0+i]
            inline_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="✅ Выполнил заказ", callback_data=f"order_executed_{callback.message.chat.id}")]
                ]
            )
            await bot.send_message(admin_id, f"👤 Новое пополнение баланса. От: {callback.message.chat.id}. @{callback.from_user.username}\n💳 Способ оплаты: CRYPTO BOT. Сумма оплаты - {insert_price} {crypto_currency} ({rub_amount:.2f}р)\n🌐 Ссылка на профиль - {profile_url[0]}", reply_markup=inline_kb)
        
        cursor.execute("UPDATE profiles SET purchases = purchases + 1 WHERE telegram_id = ?", (telegram_id,))
        conn.commit()
        
        inline_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Оплата прошла успешно", callback_data="payment_success")]
            ]
        )
        await callback.message.edit_reply_markup(reply_markup=inline_kb)
    else:
        await callback.message.reply("Оплата еще не прошла. Пожалуйста, подождите.")

async def get_invoice(id):
    returned = await crypto.get_invoices(invoice_ids=id)
    return str(returned.status)

@dp.callback_query(F.data == 'starsmethod_payment')
async def starsmethod_payment(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("На какую сумму хотите пополнить баланс?")
    await callback.answer()
    await state.set_state(Form.stars)

@dp.message(Form.stars, F.text.regexp(r'^\d+$'))
async def stars_payment(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    cursor.execute("SELECT profile_url FROM profiles WHERE telegram_id = ?", (telegram_id,))
    profile_url = cursor.fetchone()
    if profile_url and profile_url[0]:
        try:
            insert_price = int(message.text)
            price_per_star = 1.3  # цена за звезду в рублях
            stars_amount = insert_price * price_per_star
            builder = InlineKeyboardBuilder()  
            builder.button(text=f"Оплатить {insert_price}⭐️", pay=True)  
            await message.answer(f"Пополнение на: {insert_price} звезд\n({stars_amount:.2f}р) ")
            prices = [LabeledPrice(label="XTR", amount=insert_price)]
            await bot.send_invoice(
                chat_id=message.chat.id,
                title="Пополнение аккаунта на yooma.su",  
                description=f"Профиль - {profile_url[0]}",  
                provider_token="",  
                currency="XTR",  
                prices=prices,  
                start_parameter="channel_support",  
                payload="channel_support",  
                reply_markup=builder.as_markup(),
            )
        except ValueError:
            await message.answer("Пожалуйста, введите сумму для пополнения баланса.")
    else:
        await message.answer('Чтобы пополнить баланс, сначала укажите свой профиль, на который будут начисляться средства. Для этого просто нажмите на кнопку "Мой профиль"', ignore_case=True)

@dp.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):  
    await pre_checkout_query.answer(ok=True)

@dp.message(F.successful_payment)
async def process_successful_payment(message: types.Message):
    payment_amount = message.successful_payment.total_amount
    telegram_id = message.from_user.id
    cursor.execute("SELECT profile_url FROM profiles WHERE telegram_id = ?", (telegram_id,))
    profile_url = cursor.fetchone()
    price_per_star = 1.3
    rub_amount = int(payment_amount) * price_per_star
    await bot.send_message(message.chat.id, "Ваш заказ на выдачу баланса был отправлен. Ожидайте в течение суток.")
    for i in range(0, len(admin_id_list)):
        admin_id = admin_id_list[0+i]
        inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Выполнил заказ", callback_data=f"order_executed_{message.chat.id}")]
            ]
        )
        await bot.send_message(admin_id, f"👤 Новое пополнение баланса. От: {message.chat.id}. @{message.from_user.username}\n💳 Способ оплаты: TG STARS. Сумма оплаты - {payment_amount}⭐️ ({rub_amount:.2f}р)\n🌐 Ссылка на профиль - {profile_url[0]}", reply_markup=inline_kb)
    
    cursor.execute("UPDATE profiles SET purchases = purchases + 1 WHERE telegram_id = ?", (telegram_id,))
    conn.commit()

@dp.callback_query(F.data.startswith("order_executed_"))
async def order_executed(callback: types.CallbackQuery):
    chat_id = callback.data.split("_")[2]
    await bot.send_message(chat_id, "Ваш заказ был выполнен! Средства были начислены на баланс")
    await callback.answer()
    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Заказ выполнен", callback_data="order_executed_done")]
        ]
    )
    
    await callback.message.edit_reply_markup(reply_markup=inline_kb)

@dp.message(F.text == "🆘Связь с поддержкой")
async def echo(message: types.Message):
    await message.answer("Временно недоступно, пишите в личные сообщения @anarchowitz", ignore_case=True)
@dp.message(F.text == "👤Мой профиль")
async def echo(message: types.Message):
    telegram_id = message.from_user.id
    cursor.execute("SELECT profile_url, join_date, purchases FROM profiles WHERE telegram_id = ?", (telegram_id,))
    profile_info = cursor.fetchone()
    if profile_info:
        profile_url, join_date_str, purchases_count = profile_info
        if join_date_str is not None:
            join_date = datetime.strptime(join_date_str, "%Y-%m-%d %H:%M:%S%z")
            formatted_join_date = join_date.strftime("%d-%m-%Y")
        else:
            formatted_join_date = "Неизвестно"
    else:
        profile_url = "Неизвестно"
        formatted_join_date = "Неизвестно"  
        purchases_count = 0

    # Добавляем условие для проверки значения profile_url
    if profile_url is None:
        profile_url = "Неизвестно"
    if purchases_count is None:
        purchases_count = "Неизвестно"

    inline_kb_list = [
        [InlineKeyboardButton(text="📝 Изменить ссылку на профиль", callback_data='change_profile_url')],
    ]
    await message.answer(f"""
    Ваш профиль:
                             

    🆔 ID: {message.from_user.id}
    👤 Ссылка на профиль: {profile_url}

    ⏳ Вы присоединились: {formatted_join_date}
    🛒 Сделано покупок: {purchases_count}


    """, ignore_case=True, reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_kb_list))
    
@dp.callback_query(F.data == 'change_profile_url')
async def change_profile_url(callback: types.CallbackQuery):
    await callback.message.answer('Введите новую ссылку на профиль:\nНапример: https://yooma.su/profile/anarchowitz\nОтправьте ссылку в виде сообщения')
    @dp.message(F.text.startswith("https://yooma.su/profile/"))
    async def update_profile_url(message: types.Message):
        telegram_id = message.from_user.id
        profile_url = message.text
        update_profile(telegram_id, profile_url)
        await message.answer("Обновили ссылку в вашем профиле.", ignore_case=True)
        await echo(message)

def update_profile(telegram_id, profile_url):
    cursor.execute('''
        UPDATE profiles
        SET profile_url = ?
        WHERE telegram_id = ?
    ''', (profile_url, telegram_id))
    if cursor.rowcount == 0:
        cursor.execute('''
            INSERT INTO profiles (id, telegram_id, profile_url)
            VALUES (NULL, ?, ?)
        ''', (telegram_id, profile_url))
    conn.commit()

def get_crypto_rates():
    api_key = "a47a4eaf-1eab-4867-805f-6d9fd5a45b20"
    api_url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    params = {
        "symbol": ",".join(['USDT', 'TON', 'BTC', 'DOGE', 'LTC', 'ETH', 'BNB', 'TRX', 'USDC']),
        "convert": "RUB"
    }
    headers = {
        "Accepts": "application/json",
        "X-CMC_PRO_API_KEY": api_key
    }
    response = requests.get(api_url, params=params, headers=headers)
    data = response.json()
    rates = {}
    if 'data' in data:
        for symbol in data["data"]:
            rates[symbol] = data["data"][symbol]["quote"]["RUB"]["price"]
    else:
        print("Ошибка: ключ 'data' не найден в ответе API")
    return rates


async def main():
    await bot.delete_webhook(True)
    await dp.start_polling(bot, timeout=30)

if __name__ == "__main__":
    asyncio.run(main())
    
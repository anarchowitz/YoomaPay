import asyncio, logging, re, requests, uuid
from datetime import datetime
from database import conn, cursor
from dateutil import parser

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, Message, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, PreCheckoutQuery
from aiogram.types.message import ContentType
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from aiocryptopay import AioCryptoPay, Networks, exceptions

with open('tokens.txt', 'r') as file:
    tokens = file.readlines()
    tokens = [token.strip() for token in tokens]

token = tokens[0] # take it from "@botfather telegram bot"
cryptobot_token = tokens[1] # take it from "@cryptobot" - "cryptopay" - "create app/my apps" - and copy api token
admin_id_list =  ['1177915114'] # insert here your telegram id (admin_id_telegram)

#бот тг
logging.basicConfig(level=logging.INFO)
bot = Bot(token=token)
dp = Dispatcher()

#криптобот
crypto = AioCryptoPay(token=cryptobot_token, network=Networks.MAIN_NET)

class Form(StatesGroup):
    crypto = State()
    crypto_amount = State()
    stars = State()
    funpay = State()
    profile = State()


@dp.message(F.text.in_([
    "/paysupport",
    "/start",
    "💵Пополнить баланс",
    "🆘Связь с поддержкой",
    "👤Мой профиль"
]))
async def handle_commands_and_menu(message: types.Message):
    if message.text == "/paysupport":
        await message.answer("Добровольные пожертвования не подразумевают возврат средств, однако, если вы очень хотите вернуть средства - свяжитесь с нами.")
    elif message.text == "/start":
        telegram_id = message.from_user.id
        cursor.execute("SELECT join_date FROM profiles WHERE telegram_id = ?", (telegram_id,))
        join_date = cursor.fetchone()
        if not join_date:
            join_date_str = message.date.strftime("%Y-%m-%d %H:%M:%S%z")
            join_date = parser.parse(join_date_str)
            formatted_join_date = join_date.strftime("%d-%m-%Y")
            cursor.execute("INSERT INTO profiles (id, telegram_id, join_date) VALUES (NULL, ?, ?)", (telegram_id, join_date_str))
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
    if message.text == "💵Пополнить баланс":
        telegram_id = message.from_user.id
        cursor.execute("SELECT profile_url FROM profiles WHERE telegram_id = ?", (telegram_id,))
        profile_url = cursor.fetchone()
        if profile_url and profile_url[0]:
            inline_kb_list = [
                [
                    InlineKeyboardButton(text="⭐️ 1) Пополнить звездами (TG Stars)", callback_data='starsmethod_payment'),
                ],
                [
                    InlineKeyboardButton(text="🪙 2) Пополнить криптовалютой (CryptoBot)", callback_data='cryptomethod_payment'),
                ],
                [
                    InlineKeyboardButton(text="💳 3) Пополнить через FunPay", callback_data='funpaymethod_payment'),
                ],
                [
                    InlineKeyboardButton(text="📊 4) Курс пополнений", callback_data='deposit_rate')
                ]
            ]
            await message.answer("Выберите способ пополнения баланса.", ignore_case=True, reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_kb_list))
        else:
            await message.answer('Чтобы пополнить баланс, сначала укажите свой профиль, на который будут начисляться средства. Для этого просто нажмите на кнопку "Мой профиль"', ignore_case=True)
    
    elif message.text == "🆘Связь с поддержкой":
        await message.answer("Временно недоступно, пишите в личные сообщения @anarchowitz", ignore_case=True)

    elif message.text == "👤Мой профиль":
            telegram_id = message.from_user.id
            cursor.execute("SELECT profile_url, join_date, purchases, promocode FROM profiles WHERE telegram_id = ?", (telegram_id,))
            profile_info = cursor.fetchone()
            if profile_info:
                profile_url, join_date_str, purchases_count, promocode = profile_info
                if join_date_str is not None:
                    join_date = datetime.strptime(join_date_str, "%Y-%m-%d %H:%M:%S%z")
                    formatted_join_date = join_date.strftime("%d.%m.%Y")
                else:
                    formatted_join_date = "Неизвестно"
            else:
                profile_url = "Неизвестно"
                formatted_join_date = "Неизвестно"
                purchases_count = 0
                promocode = "Неизвестно"

            if profile_url is None:
                profile_url = "Неизвестно"
            if purchases_count is None:
                purchases_count = "Неизвестно"
            if promocode is None:
                promocode = "Нету"

            inline_kb_list = [
                [InlineKeyboardButton(text="📝 Изменить ссылку на профиль", callback_data='change_profile_url')],
                [InlineKeyboardButton(text="🎁 Использовать промокод", callback_data='use_promocode')]
            ]
            await message.answer(f"""
            <b>Ваш профиль:</b>

            🆔 ID: <code>{message.from_user.id}</code>
            👤 Ссылка на профиль: <a href="{profile_url}">{profile_url}</a>

            ⏳ Вы присоединились: {formatted_join_date}
            🛒 Сделано покупок: {purchases_count}
            🎁 Примененный промокод: {promocode}

            """, parse_mode="HTML", disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_kb_list))

@dp.callback_query(F.data == 'use_promocode')
async def use_promocode(callback: types.CallbackQuery):
    await callback.message.answer("Введите промокод:")
    await callback.answer()
    @dp.message(F.text.regexp(r'^[А-Я]+$'))
    async def enter_promocode(message: types.Message):
        promocode = message.text
        telegram_id = message.from_user.id
        discount = check_promocode(promocode, telegram_id)
        if discount:
            await message.answer(f"Промокод '{promocode}' применен. Бонус к пополнению: {discount}%")
            cursor.execute("UPDATE profiles SET promocode = ? WHERE telegram_id = ?", (promocode, telegram_id))
            conn.commit()
        else:
            await message.answer("Промокод неверен или уже использован")

@dp.callback_query(F.data == 'funpaymethod_payment')
async def funpaymethod_payment(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("На какую сумму хотите пополнить баланс?")
    await callback.answer()
    await state.set_state(Form.funpay)

@dp.message(Form.funpay, F.text.regexp(r'^\d+(\.\d+)?$'))
async def funpay_amount(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    cursor.execute("SELECT profile_url FROM profiles WHERE telegram_id = ?", (telegram_id,))
    profile_url = cursor.fetchone()
    if profile_url and profile_url[0]:
        try:
            insert_price = int(message.text)
            if insert_price < 150:
                await message.answer("⚠️ Минимальная сумма пополнения - 150 рублей.")
                return
            inline_kb_list = [
                [
                    InlineKeyboardButton(text="✅ Начать пополнение", callback_data='start_funpay'),
                    InlineKeyboardButton(text="❌ Отменить", callback_data='cancel_funpay')
                ]
            ]
            await message.answer(f"👤 Ваша ссылка на профиль: {profile_url[0]}\n💵 Сумма пополнения: {insert_price}р", reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_kb_list))
            await state.update_data(insert_price=insert_price, profile_url=profile_url[0])
        except ValueError:
            await message.answer("Пожалуйста, введите сумму для пополнения баланса.")
    else:
        await message.answer('Чтобы пополнить баланс, сначала укажите свой профиль, на который будут начисляться средства. Для этого просто нажмите на кнопку "Мой профиль"', ignore_case=True)

@dp.callback_query(F.data == 'start_funpay')
async def start_funpay(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    insert_price = data.get('insert_price')
    profile_url = data.get('profile_url')
    telegram_id = callback.from_user.id
    await callback.message.answer("Ваш заказ был отправлен. Ожидайте ссылку на оплату.")
    payment_id = str(uuid.uuid4().hex[:6])
    for i in range(0, len(admin_id_list)):
        admin_id = admin_id_list[0+i]
        inline_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="✅ Выполнить", callback_data=f"order_funpay_executed_{callback.message.chat.id}_{payment_id}"),
                 InlineKeyboardButton(text="❌ Отменить", callback_data=f"order_canceled_{callback.message.chat.id}_{payment_id}"),
                ],
                [InlineKeyboardButton(text="Указать ссылку на оплату", callback_data=f"set_payment_link_{callback.message.chat.id}_{payment_id}")
                ]
            ]
        )
        await bot.send_message(admin_id, f"👤 Новое пополнение баланса. От: {callback.message.chat.id}. @{callback.from_user.username}\n💳 Способ оплаты: FUNPAY. Сумма оплаты - {insert_price}р\n🌐 Ссылка на профиль - {profile_url}\n📝 ID платежа: #{payment_id}", reply_markup=inline_kb)
    await callback.answer()
    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Пополнение было начато", callback_data="unclickablebutton")]
        ]
    )
    await callback.message.edit_reply_markup(reply_markup=inline_kb)


@dp.callback_query(F.data.startswith("set_payment_link_"))
async def set_payment_link(callback: types.CallbackQuery, state: FSMContext):
    data_parts = callback.data.split("_")
    chat_id = data_parts[3]
    payment_id = data_parts[4]
    await state.update_data(chat_id=chat_id, payment_id=payment_id)
    await bot.send_message(callback.message.chat.id, "Укажите ссылку на оплату баланса:")

    @dp.message(F.text.startswith("https://funpay.com/lots/offer?id="))
    async def send_payment_link(message: types.Message, state: FSMContext):
        data = await state.get_data()
        chat_id = data.get('chat_id')
        payment_id = data.get('payment_id')
        await bot.send_message(callback.message.chat.id, f"Отправил ссылку пользователю: {chat_id}, {payment_id}")
        await bot.send_message(chat_id, f"Ссылка на оплату баланса: {message.text}", reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="✅ Оплатил", callback_data=f"paid_order_{payment_id}")]
            ]
        ))


@dp.callback_query(F.data.startswith("paid_order_"))
async def paid_order(callback: types.CallbackQuery):
    payment_id = callback.data.split("_")[2]
    await callback.message.answer("В течение суток вам будет выдан баланс, если вы указали все правильно.")
    chat_id = callback.message.chat.id
    for i in range(0, len(admin_id_list)):
        admin_id = admin_id_list[0+i]
        await bot.send_message(admin_id, f"👤 От: {callback.message.chat.id}. @{callback.from_user.username}. \nОплатил заказ\n📝 ID платежа: #{payment_id}")
    
    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Оплачено", callback_data="unclickablebutton")]
        ]
    )
    await callback.message.edit_reply_markup(reply_markup=inline_kb)
@dp.callback_query(F.data.startswith("order_canceled_"))
async def order_canceled(callback: types.CallbackQuery):
    data_parts = callback.data.split("_")
    chat_id = data_parts[2]
    payment_id = data_parts[3]
    await bot.send_message(callback.message.chat.id, f"Заказ (#{payment_id}) был отменен")
    await bot.send_message(chat_id, "Ваш заказ был отменен. Возможно, ссылка на профиль недействительна или вы неверно указали информацию об оплате.")
    await callback.answer()
    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Заказ отменен", callback_data="order_canceled_done")]
        ]
    )
    await callback.message.edit_reply_markup(reply_markup=inline_kb)

@dp.callback_query(F.data == 'cancel_funpay')
async def cancel_funpay(callback: types.CallbackQuery):
    await callback.answer()
    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Пополнение было отменено", callback_data="unclickablebutton")]
        ]
    )
    await callback.message.edit_reply_markup(reply_markup=inline_kb)

@dp.callback_query(F.data == 'deposit_rate')
async def deposit_rate(callback: types.CallbackQuery):
    await callback.answer()
    rates, star_price_rub = get_crypto_rates()
    message_text = "📊 Курс валют:\n\n"
    message_text += f"1 Звезда = {star_price_rub:.2f} RUB\n\n"
    for currency, rate in rates.items():
        message_text += f"1 {currency} = {rate:.2f} RUB\n"
    await callback.message.answer(message_text)
    await callback.message.answer('\nСовет: звезды дешевле всего можно купить в https://fragment.com/stars/buy')

@dp.callback_query(F.data == 'cryptomethod_payment')
async def cryptomethod_payment(callback: types.CallbackQuery, state: FSMContext):
    inline_kb_list = [
        [
            InlineKeyboardButton(text="📚Гайд как пополнять криптовалютой", callback_data="cryptoguide"),
        ],
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
    await state.set_state(Form.crypto)

@dp.callback_query(F.data == 'cryptoguide')
async def crypto_guide(callback: types.CallbackQuery):
    await callback.message.answer("Ссылка на гайд -> https://teletype.in/@anarchowitz/yoomapay_crypto")

@dp.callback_query(F.data.in_(['USDT', 'TON', 'BTC', 'DOGE', 'LTC', 'ETH', 'BNB', 'TRX', 'USDC']))
async def crypto_currency(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer('Пожалуйста, введите сумму для пополнения баланса: \n (К примеру: 1.25)')
    await state.update_data(crypto_currency=callback.data)
    await state.set_state(Form.crypto_amount)

@dp.message(Form.crypto_amount, F.text.regexp(r'^\d+(\.\d+)?$'))
async def crypto_amount(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    cursor.execute("SELECT profile_url, promocode FROM profiles WHERE telegram_id = ?", (telegram_id,))
    profile_info = cursor.fetchone()
    if profile_info:
        profile_url, promocode = profile_info
        if profile_url:
            try:
                insert_price = float(message.text)
                data = await state.get_data()
                crypto_currency = data.get('crypto_currency')
                try:
                    invoice = await crypto.create_invoice(asset=crypto_currency, amount=insert_price, allow_anonymous=False, allow_comments=False, hidden_message="Техническая поддержка: @anarchowitz")
                except exceptions.CodeErrorFactory as e:
                    if e.code == 400:
                        await message.answer("⚠️ Недопустимая сумма. Пожалуйста, попробуйте еще раз.")
                    else:
                        await message.answer("⚠️ Произошла ошибка. Пожалуйста, попробуйте еще раз.")
                    return
                pay_url = invoice.bot_invoice_url
                invoice_id = invoice.invoice_id
                if promocode:
                    discount = check_promocode(promocode, telegram_id)
                    if discount:
                        await message.answer(f"Промокод '{promocode}' применен. Бонус к пополнению: {discount}%")
                await message.answer(f"Сумма пополнения: {insert_price} {crypto_currency}")
                inline_kb = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="Проверить оплату", callback_data="cryptocheck_payments")]
                    ]
                )
                await message.answer(f"Ссылка для пополнения: \n{pay_url}", reply_markup=inline_kb)
                await state.update_data(invoice_id=invoice_id, insert_price=insert_price, promocode=promocode)
            except ValueError:
                await message.answer("Пожалуйста, введите сумму для пополнения баланса.")
        else:
            await message.answer('Чтобы пополнить баланс, сначала укажите свой профиль, на который будут начисляться средства. Для этого просто нажмите на кнопку "Мой профиль"', ignore_case=True)
    else:
        await message.answer('Чтобы пополнить баланс, сначала укажите свой профиль, на который будут начисляются средства. Для этого просто нажмите на кнопку "Мой профиль"', ignore_case=True)

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
        await bot.send_message(callback.message.chat.id, "Ваш заказ на выдачу баланса был отправлен. Ожидайте в течение суток.")
        crypto_rates, _ = get_crypto_rates()
        rub_amount = insert_price * crypto_rates[crypto_currency]
        promocode = data.get('promocode')
        if promocode:
            discount = check_promocode(promocode, telegram_id)
            if discount:
                bonus_amount = rub_amount * (discount / 100)
                total_amount = rub_amount + bonus_amount
                for i in range(0, len(admin_id_list)):
                    admin_id = admin_id_list[0+i]
                    inline_kb = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="✅ Выполнил заказ", callback_data=f"order_executed_{callback.message.chat.id}")]
                        ]
                    )
                    await bot.send_message(admin_id, f"👤 Новое пополнение баланса. От: {callback.message.chat.id}. @{callback.from_user.username}\n💳 Способ оплаты: CRYPTO BOT. Сумма оплаты - {insert_price} {crypto_currency} ({total_amount:.2f}р)\n🌐 Ссылка на профиль - {profile_url[0]}\n🎁 Промокод: {promocode} ({discount}% бонус)", reply_markup=inline_kb)
                cursor.execute("SELECT telegram_id_used_promo FROM promocodes WHERE code = ?", (promocode,))
                telegram_id_used_promo = cursor.fetchone()[0]
                if telegram_id_used_promo:
                    telegram_id_used_promo += ',' + str(telegram_id)
                else:
                    telegram_id_used_promo = str(telegram_id)
                cursor.execute("UPDATE promocodes SET used = used + 1, telegram_id_used_promo = ? WHERE code = ?", (telegram_id_used_promo, promocode))
                conn.commit()
                cursor.execute("UPDATE profiles SET promocode = NULL WHERE telegram_id = ?", (telegram_id,))
                conn.commit()
            else:
                for i in range(0, len(admin_id_list)):
                    admin_id = admin_id_list[0+i]
                    inline_kb = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="✅ Выполнил заказ", callback_data=f"order_executed_{callback.message.chat.id}")]
                        ]
                    )
                    await bot.send_message(admin_id, f"👤 Новое пополнение баланса. От: {callback.message.chat.id}. @{callback.from_user.username}\n💳 Способ оплаты: CRYPTO BOT. Сумма оплаты - {insert_price} {crypto_currency} ({rub_amount:.2f}р)\n🌐 Ссылка на профиль - {profile_url[0]}\n🎁 Промокод: {promocode} ({discount}% бонус)", reply_markup=inline_kb)
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
    await callback.message.answer("Сколько звезд хотите потратить?")
    await state.set_state(Form.stars)

@dp.message(Form.stars, F.text.regexp(r'^\d+$'))
async def stars_payment(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    cursor.execute("SELECT profile_url, promocode FROM profiles WHERE telegram_id = ?", (telegram_id,))
    profile_info = cursor.fetchone()
    if profile_info:
        profile_url, promocode = profile_info
        if profile_url:
            try:
                insert_price = int(message.text)
                if insert_price > 100000:
                    await message.answer("⚠️ Максимальная сумма пополнения - 100.000 звезд.")
                    return
                elif insert_price < 1:
                    await message.answer("⚠️ Минимальная сумма пополнения - 1 звезда.")
                    return
                _, star_price_rub = get_crypto_rates()
                if promocode:
                    discount = check_promocode(promocode, telegram_id)  # передаем telegram_id
                    if discount:
                        stars_amount = insert_price * star_price_rub
                        bonus_amount = stars_amount * (discount / 100)
                        total_amount = stars_amount + bonus_amount
                        await message.answer(f'Промокод "{promocode}" применен. Бонус к пополнению: {discount}%')
                    else:
                        total_amount = insert_price * star_price_rub
                else:
                    total_amount = insert_price * star_price_rub
                builder = InlineKeyboardBuilder()  
                builder.button(text=f"Оплатить {insert_price}⭐️", pay=True)  
                await message.answer(f"Пополнение на: {insert_price} звезд\n(Вам придет: {total_amount:.2f}р) ")
                prices = [LabeledPrice(label="XTR", amount=insert_price)]
                await bot.send_invoice(
                    chat_id=message.chat.id,
                    title="Пополнение аккаунта на yooma.su",  
                    description=f"Профиль - {profile_url}",  
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
    else:
        await message.answer('Чтобы пополнить баланс, сначала укажите свой профиль, на который будут начисляться средства. Для этого просто нажмите на кнопку "Мой профиль"', ignore_case=True)

@dp.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):  
    await pre_checkout_query.answer(ok=True)

@dp.message(F.successful_payment)
async def process_successful_payment(message: types.Message):
    payment_amount = message.successful_payment.total_amount
    telegram_id = message.from_user.id
    cursor.execute("SELECT profile_url, promocode FROM profiles WHERE telegram_id = ?", (telegram_id,))
    profile_info = cursor.fetchone()
    if profile_info:
        profile_url, promocode = profile_info
        _, star_price_rub = get_crypto_rates()
        rub_amount = int(payment_amount) * star_price_rub
        if promocode:
            discount = check_promocode(promocode, telegram_id)
            if discount:
                bonus_amount = rub_amount * (discount / 100)
                total_amount = rub_amount + bonus_amount
                for i in range(0, len(admin_id_list)):
                    admin_id = admin_id_list[0+i]
                    inline_kb = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="✅ Выполнил заказ", callback_data=f"order_executed_{message.chat.id}")]
                        ]
                    )
                    await bot.send_message(admin_id, f"👤 Новое пополнение баланса. От: {message.chat.id}. @{message.from_user.username}\n💳 Способ оплаты: TG STARS. Сумма оплаты - {payment_amount}⭐️ ({total_amount:.2f}р)\n🌐 Ссылка на профиль - {profile_url}\n🎁 Промокод: {promocode} ({discount}% бонус)", reply_markup=inline_kb)
                cursor.execute("UPDATE profiles SET promocode = NULL WHERE telegram_id = ?", (telegram_id,))
                conn.commit()
                cursor.execute("SELECT telegram_id_used_promo FROM promocodes WHERE code = ?", (promocode,))
                telegram_id_used_promo = cursor.fetchone()[0]
                if telegram_id_used_promo:
                    telegram_id_used_promo += ',' + str(telegram_id)
                else:
                    telegram_id_used_promo = str(telegram_id)
                cursor.execute("UPDATE promocodes SET used = used + 1, telegram_id_used_promo = ? WHERE code = ?", (telegram_id_used_promo, promocode))
                conn.commit()
            else:
                for i in range(0, len(admin_id_list)):
                    admin_id = admin_id_list[0+i]
                    inline_kb = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="✅ Выполнил заказ", callback_data=f"order_executed_{message.chat.id}")]
                        ]
                    )
                    await bot.send_message(admin_id, f"👤 Новое пополнение баланса. От: {message.chat.id}. @{message.from_user.username}\n💳 Способ оплаты: TG STARS. Сумма оплаты - {payment_amount}⭐️ ({rub_amount:.2f}р)\n🌐 Ссылка на профиль - {profile_url}", reply_markup=inline_kb)
        cursor.execute("UPDATE profiles SET purchases = purchases + 1 WHERE telegram_id = ?", (telegram_id,))
        conn.commit()

@dp.callback_query(F.data.startswith("order_executed_"))
async def order_executed(callback: types.CallbackQuery):
    chat_id = callback.data.split("_")[2]
    await bot.send_message(chat_id, "Ваш заказ был выполнен! Средства были начислены на баланс")
    await callback.answer()
    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Заказ выполнен", callback_data="unclickablebutton")]
        ]
    )
    
    await callback.message.edit_reply_markup(reply_markup=inline_kb)

@dp.callback_query(F.data.startswith("order_funpay_executed_"))
async def order_executed(callback: types.CallbackQuery):
    chat_id = callback.data.split("_")[3]
    await bot.send_message(chat_id, "Ваш заказ был выполнен! Средства были начислены на баланс")
    await bot.send_message(chat_id, "Не забудьте подтвердить заказ на фанпей! В противном случае через сутки ваши средства могут быть утеряны!")
    await callback.answer()
    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Заказ выполнен", callback_data="unclickablebutton")]
        ]
    )
    
    await callback.message.edit_reply_markup(reply_markup=inline_kb)
    
@dp.callback_query(F.data == 'change_profile_url')
async def change_profile_url(callback: types.CallbackQuery):
    await callback.message.answer('Введите новую ссылку на профиль:\nНапример: https://yooma.su/ru/profile/admin\nОтправьте ссылку в виде сообщения')
    @dp.message(F.text.startswith("https://yooma.su/ru/profile/") or F.text.startswith("https://yooma.su/en/profile/"))
    async def update_profile_url(message: types.Message):
        telegram_id = message.from_user.id
        profile_url = message.text
        if profile_url == "https://yooma.su/ru/profile/admin":
            await message.answer('Вам нужно ввести вашу личную ссылку на профиль!')
            return
        else:
            update_profile(telegram_id, profile_url)
            await message.answer("Обновили ссылку в вашем профиле.", ignore_case=True)

def update_profile(telegram_id, profile_url):
    cursor.execute('''UPDATE profiles SET profile_url = ? WHERE telegram_id = ?''', (profile_url, telegram_id))
    if cursor.rowcount == 0:
        cursor.execute('''INSERT INTO profiles (id, telegram_id, profile_url) VALUES (NULL, ?, ?)''', (telegram_id, profile_url))
    conn.commit()
    cursor.execute("SELECT promocode FROM profiles WHERE telegram_id = ?", (telegram_id,))
    promocode = cursor.fetchone()
    if promocode and promocode[0]:
        cursor.execute("UPDATE promocodes SET telegram_id_used_promo = ? WHERE code = ?", (str(telegram_id), promocode[0]))
        conn.commit()

def get_crypto_rates():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "toncoin,tether,bitcoin,dogecoin,litecoin,ethereum,binancecoin,tron,usd-coin",
        "vs_currencies": "rub"
    }

    response = requests.get(url, params=params)
    data = response.json()

    rates = {}
    for currency, price in data.items():
        if currency == "tron":
            rates["TRX"] = price["rub"]
        else:
            rates[currency] = price["rub"]

    usdt_rub = rates["tether"]
    usd_rub = usdt_rub
    star_price_usd = 0.015
    star_price_rub = star_price_usd * usd_rub

    return rates, star_price_rub

def check_promocode(promocode, telegram_id):
    cursor.execute("SELECT * FROM promocodes WHERE code = ?", (promocode,))
    promocode_data = cursor.fetchone()
    if promocode_data:
        expiration_date = datetime.strptime(promocode_data[3], "%Y-%m-%d")
        if promocode_data[6] is not None and datetime.now() <= expiration_date and promocode_data[4] < int(promocode_data[6]):
            cursor.execute("SELECT telegram_id_used_promo FROM promocodes WHERE code = ?", (promocode,))
            telegram_id_used_promo = cursor.fetchone()[0]
            if telegram_id_used_promo:
                if str(telegram_id) in telegram_id_used_promo.split(','):
                    return None
            return int(promocode_data[2])
        else:
            return None  # промокод уже использован или срок действия истек
    else:
        return None  # промокод не существует


@dp.message(F.text.regexp(r'^(?!https?://(yooma\.su|funpay\.com)/?.*)$'))
async def echo(message: types.Message):
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
    await message.answer("Неизвестная команда!\nНажми на нужную кнопку ниже 👇", reply_markup=keyboard)

async def main():
    try:
        await bot.delete_webhook(True)
        await dp.start_polling(bot, timeout=30)
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main())
    
import asyncio, logging, re, requests

from datetime import datetime

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, Message, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, PreCheckoutQuery
from aiogram.types.message import ContentType
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from database import conn, cursor


class Form(StatesGroup):
    crypto = State()
    stars = State()
    profile = State()

token = "7939037867:AAHhuUFYN0nSkbf2ktN4a2c-Ab-R2dVg5-A"
admin_id_list =  ['1177915114', '947603836']
parameters = {
    "token": "30283:AAAtUrEajzoZQX0iYjC58NJtTbfL520Q0Us",
    "api_url": "https://testnet-pay.crypt.bot/"
}

logging.basicConfig(level=logging.INFO)
bot = Bot(token=token)
dp = Dispatcher()


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
                InlineKeyboardButton(text="💸 2) Пополнить криптовалютой (Чек/Перевод)", callback_data='cryptomethod_payment')
            ]
        ]
        await message.answer("Выберите способ пополнения баланса.", ignore_case=True, reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_kb_list))
    else:
        await message.answer('Чтобы пополнить баланс, сначала укажите свой профиль, на который будут начисляться средства. Для этого просто нажмите на кнопку "Мой профиль"', ignore_case=True)

@dp.callback_query(F.data == 'cryptomethod_payment')
async def cryptomethod_payment(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("На какую сумму хотите пополнить баланс?")
    await callback.answer()
    await state.set_state(Form.crypto)

@dp.message(Form.crypto)
async def crypto_payment(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    cursor.execute("SELECT profile_url FROM profiles WHERE telegram_id = ?", (telegram_id,))
    profile_url = cursor.fetchone()
    if profile_url and profile_url[0]:
        try:
            insert_price = float(re.search(r'\d+(?:\.\d+)?', message.text).group())
            cryptopay = CryptoPay(telegram_id, parameters)
            invoice_info = cryptopay.create_invoice(amount=insert_price, asset='DOGE')
            pay_url = invoice_info['result']['pay_url']
            await message.answer(f"Сумма пополнения: {insert_price} DOGE\nСсылка для пополнения: \n{pay_url}")
        except ValueError:
            await message.answer("Пожалуйста, введите сумму для пополнения баланса.")
    else:
        await message.answer('Чтобы пополнить баланс, сначала укажите свой профиль, на который будут начисляться средства. Для этого просто нажмите на кнопку "Мой профиль"', ignore_case=True)

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


async def main():
    await bot.delete_webhook(True)
    await dp.start_polling(bot, timeout=30)

if __name__ == "__main__":
    asyncio.run(main())
    
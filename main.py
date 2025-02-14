import asyncio, logging, re

from datetime import datetime

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, Message, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, PreCheckoutQuery
from aiogram.types.message import ContentType
from aiogram.utils.keyboard import InlineKeyboardBuilder  

from database import conn, cursor

token = "7939037867:AAHhuUFYN0nSkbf2ktN4a2c-Ab-R2dVg5-A"
admin_id_list =  ['1177915114', '947603836']
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
                InlineKeyboardButton(text="💸 2) Пополнить криптовалютой (Чек/Перевод)", callback_data='cryptomethod_payment')
            ]
        ]
        await message.answer("Выберите способ пополнения баланса.", ignore_case=True, reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_kb_list))
    else:
        await message.answer('Чтобы пополнить баланс, сначала укажите свой профиль, на который будут начисляться средства. Для этого просто нажмите на кнопку "Мой профиль"', ignore_case=True)

@dp.callback_query(F.data == 'starsmethod_payment')
async def starsmethod_payment(callback: types.CallbackQuery):
    await callback.message.answer("На какую сумму хотите пополнить баланс?")
    await callback.answer()

    @dp.message(F.text)
    async def echo(message: types.Message):
        telegram_id = message.from_user.id
        cursor.execute("SELECT profile_url FROM profiles WHERE telegram_id = ?", (telegram_id,))
        profile_url = cursor.fetchone()
        if profile_url and profile_url[0]:
            try:
                number = int(re.search(r'\d+', message.text).group())
                price_per_star = 1.3  # цена за звезду в рублях
                stars_amount = number * price_per_star
                builder = InlineKeyboardBuilder()  
                builder.button(text=f"Оплатить {number}⭐️", pay=True)  
                await message.answer(f"Пополнение на: {number} звезд\n({stars_amount:.2f}р)")
                prices = [LabeledPrice(label="XTR", amount=number)]
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
            except AttributeError:
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
        join_date = datetime.strptime(join_date_str, "%Y-%m-%d %H:%M:%S%z")
        formatted_join_date = join_date.strftime("%d-%m-%Y")
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
    
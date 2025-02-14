import asyncio, logging, re

from datetime import datetime

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, Message, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, PreCheckoutQuery
from aiogram.types.message import ContentType
from aiogram.utils.keyboard import InlineKeyboardBuilder  

from database import conn, cursor

token = "7939037867:AAHhuUFYN0nSkbf2ktN4a2c-Ab-R2dVg5-A"
# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)
# Объект бота
bot = Bot(token=token)
# Диспетчер
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
        cursor.execute("UPDATE profiles SET join_date = ? WHERE telegram_id = ?", (message.date, telegram_id))
        conn.commit()
    
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
                number = re.search(r'\d+', message.text).group()
                builder = InlineKeyboardBuilder()  
                builder.button(text=f"Оплатить {number}⭐️", pay=True)  
                await message.answer(f"Пополнение на: {number} звезд")
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
    await bot.send_message(message.chat.id, "Ваш заказ на выдачу баланса был отправлен. Ожидайте в течение суток.")
    await bot.send_message(admin_id, "Ваш заказ на выдачу баланса был отправлен. Ожидайте в течение суток.")
    

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


# Запуск процесса поллинга новых апдейтов
async def main():
    await dp.start_polling(bot, timeout=30)

if __name__ == "__main__":
    asyncio.run(main())
    
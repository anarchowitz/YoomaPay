# 💳 YoomaPay - Payment Bot  

**Лучший бот для альтернативного пополнения баланса на [yooma.su](https://yooma.su)**  
*Удобный, безопасный и полностью автоматизированный способ депозита через криптовалюты*  

[![Sponsored By](https://img.shields.io/badge/Sponsored_By-yooma.su-FF6F61?logo=github-sponsors)](https://yooma.su)  

[![Telegram Contact](https://img.shields.io/badge/Contact-Telegram-blue?logo=telegram)](https://t.me/anarchowitz)  [![RU Language](https://img.shields.io/badge/Language-RU-red)](https://yooma.su)  [![Open Source](https://img.shields.io/badge/License-MIT-yellow?logo=open-source-initiative)](https://opensource.org/licenses/MIT)  

[![SQLite](https://img.shields.io/badge/SQLite-✓-003B57?logo=sqlite)](https://sqlite.org)  [![Python](https://img.shields.io/badge/Python-✓-3776AB?logo=python)](https://python.org)  [![Aiogram](https://img.shields.io/badge/Aiogram-✓-2CA5E0?logo=telegram)](https://docs.aiogram.dev)  [![CryptoPay](https://img.shields.io/badge/CryptoPay-✓-4CCD99?logo=bitcoin)](https://aiocryptopay.readthedocs.io)  

## 🌟 Особенности  
- 💸 Поддержка множества криптовалют (BTC, USDT, ETH и др.)  
- 🔐 Безопасные транзакции через CryptoPay API  
- 📊 Данные пользователей в SQLite базе  
- 📝 Логирование всех действий (logging)  
- ⚡ Асинхронная работа (asyncio) для максимальной производительности  
- 🤖 Удобный Telegram-интерфейс через aiogram  

## 📥 Установка  

### Требования  
- Python 3.8+  
- [Telegram Bot Token](https://core.telegram.org/bots#how-do-i-create-a-bot)  
- [CryptoPay API Key](https://help.crypt.bot/crypto-pay-api)
- [Telegram Chat ID](https://t.me/chatIDrobot)

### Пошаговая инструкция  
1. **Установите зависимости**:
  ```
  pip install aiogram
  pip install aiocryptopay
  pip install sqlite3
  pip install logging
  pip install asyncio
  pip install dateparser
  pip install uuid
  ```
2. **Настройте конфигурацию:**
   Откройте tokens.txt и впишите токены вместо **1** и **2** строки.
  ```
here_your_telegrambot_token
here_your_cryptobot_token
  ```
3. **Запустите бота:**
  ```
  python main.py
  ```

## ⚙️ Основные команды
/start - Открыть главное меню
/paysupport - требование телеграмма для оплаты звездами. (useless)

## 🔧 Кастомизация
Для индивидуальной настройки или интеграции с вашей системой:
[**Telegram: @anarchowitz**](https://t.me/anarchowitz)

## 📄 Лицензия

Проект распространяется под лицензией [MIT License](https://github.com/Anarchowitz/YoomaPay/blob/main/LICENSE).
При поддержке [yooma.su](https://yooma.su/ru)

# [![Star on GitHub](https://img.shields.io/github/stars/anarchowitz/YoomaPay.svg?style=social)](https://github.com/anarchowitz/YoomaPay/stargazers)

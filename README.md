# 💳 YoomaPay - Payment Bot  

**Лучший бот для альтернативного пополнения баланса на [yooma.su](https://yooma.su)**  
*Удобный, безопасный и полностью автоматизированный способ депозита через криптовалюты*  

[![Sponsored By](https://img.shields.io/badge/Sponsored_By-yooma.su-FF6F61?logo=github-sponsors)](https://yooma.su)  

[![Telegram Contact](https://img.shields.io/badge/Contact-Telegram-blue?logo=telegram)](https://t.me/anarchowitz)  
[![RU Language](https://img.shields.io/badge/Language-RU-red)](https://yooma.su)  
[![Open Source](https://img.shields.io/badge/License-MIT-yellow?logo=open-source-initiative)](https://opensource.org/licenses/MIT)  

[![SQLite](https://img.shields.io/badge/SQLite-✓-003B57?logo=sqlite)](https://sqlite.org)  
[![Python](https://img.shields.io/badge/Python-✓-3776AB?logo=python)](https://python.org)  
[![Aiogram](https://img.shields.io/badge/Aiogram-✓-2CA5E0?logo=telegram)](https://docs.aiogram.dev)  
[![CryptoPay](https://img.shields.io/badge/CryptoPay-✓-4CCD99?logo=bitcoin)](https://aiocryptopay.readthedocs.io)  

## 🌟 Особенности  
- 💸 Поддержка множества криптовалют (BTC, USDT, ETH и др.)  
- 🔐 Безопасные транзакции через CryptoPay API  
- 📊 Полная история операций в SQLite базе  
- 📝 Логирование всех действий (logging)  
- ⚡ Асинхронная работа (asyncio) для максимальной производительности  
- 🤖 Удобный Telegram-интерфейс через aiogram  

## 📥 Установка  

### Требования  
- Python 3.8+  
- [Telegram Bot Token](https://core.telegram.org/bots#how-do-i-create-a-bot)  
- [CryptoPay API Key](https://help.crypt.bot/crypto-pay-api)  

### Пошаговая инструкция  
1. **Установите зависимости**:  
  ```bash
  pip install aiogram aiocryptopay sqlite3 logging asyncio

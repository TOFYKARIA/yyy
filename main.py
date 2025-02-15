from telethon import TelegramClient, events, functions, types
import asyncio
import time
import random
import aiohttp
import logging

# Конфигурация
prefixes = ['.', '/', '!', '-']
logger = logging.getLogger(__name__)

async def setup_client():
    print("Добро пожаловать в ShadowBot!")
    print("Для начала работы нужно настроить API.")
    print("Получите API данные на my.telegram.org")
    api_id = input("Введите API ID: ")
    api_hash = input("Введите API Hash: ")
    return TelegramClient('session_name', api_id, api_hash)

@events.register(events.NewMessage(pattern=f'[{"".join(prefixes)}]help'))
async def help_handler(event):
    """Показывает список всех команд"""
    help_text = """🔱 UGCLAWS USERBOT 🔱

Доступные команды:
• 💧.help - показать это сообщение
• 💧.anime [nsfw] - отправить случайное аниме фото
• 💧.im [режим] - запустить имитацию (режимы: typing/voice/video/game/mixed)
• 💧.imstop - остановить имитацию
• 💧.mozg [yes/no] - включить/выключить MegaMozg
• 💧.mozgchance [число] - установить шанс ответа MegaMozg (1 к N)
• 💧.time - включить/выключить время в нике
• 💧.time_msk - установить московское время
• 💧.time_ekb - установить екатеринбургское время 
• 💧.time_omsk - установить омское время
• 💧.time_samara - установить самарское время"""

    await event.edit(help_text)

@events.register(events.NewMessage(pattern=f'[{"".join(prefixes)}]anime'))
async def anime_handler(event):
    """Отправляет случайное аниме фото"""
    args = event.raw_text.split()
    if len(args) > 1 and args[1].lower() == "nsfw":
        url = "https://api.waifu.pics/nsfw/waifu"
        caption = "🎗Лови NSFW фото!"
    else:
        url = "https://api.waifu.pics/sfw/waifu"
        caption = "🔮Случайное аниме фото!"

    message = await event.respond("ван сек..")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if "url" in data:
                        await event.client.send_file(event.chat_id, data["url"], caption=caption)
                        await message.delete()
                    else:
                        await message.edit("Ошибка: не удалось найти URL в ответе.")
                else:
                    await message.edit(f"Ошибка: {response.status}")
    except Exception as e:
        await message.edit(f"Ошибка: {e}")

@events.register(events.NewMessage(pattern=f'[{"".join(prefixes)}]im'))
async def im_handler(event):
    """Запустить имитацию: .im <режим>
    Режимы: typing/voice/video/game/mixed"""

    args = event.raw_text.split()[1] if len(event.raw_text.split()) > 1 else "mixed"
    mode = args.lower()
    chat_id = event.chat_id

    if chat_id in _imitation_active and _imitation_active[chat_id]:
        await event.edit("❌ Имитация уже запущена")
        return

    _imitation_active[chat_id] = True

    _imitation_tasks[chat_id] = asyncio.create_task(
        _imitate(event.client, chat_id, mode)
    )

    await event.edit(f"🎭 Имитация запущена\nРежим: {mode}")

_imitation_tasks = {}
_imitation_active = {}

async def _imitate(client, chat_id, mode):
    """Бесконечная имитация действия"""
    try:
        while _imitation_active.get(chat_id, False):
            if mode == "typing":
                async with client.action(chat_id, 'typing'):
                    await asyncio.sleep(5)
            elif mode == "voice":
                async with client.action(chat_id, 'record-audio'):
                    await asyncio.sleep(5)
            elif mode == "video":
                async with client.action(chat_id, 'record-video'):
                    await asyncio.sleep(5)
            elif mode == "game":
                async with client.action(chat_id, 'game'):
                    await asyncio.sleep(5)
            elif mode == "mixed":
                actions = ['typing', 'record-audio', 'record-video', 'game']
                async with client.action(chat_id, random.choice(actions)):
                    await asyncio.sleep(5)
    except Exception as e:
        logger.error(f"Imitation error: {e}")
        _imitation_active[chat_id] = False

@events.register(events.NewMessage(pattern=f'[{"".join(prefixes)}]imstop'))
async def imstop_handler(event):
    """Остановить имитацию"""
    chat_id = event.chat_id

    if chat_id in _imitation_active:
        _imitation_active[chat_id] = False
        if chat_id in _imitation_tasks:
            _imitation_tasks[chat_id].cancel()
            del _imitation_tasks[chat_id]

    await event.edit("🚫 Имитация остановлена")

async def is_connected(client):
    """Проверка, подключен ли клиент к Telegram"""
    try:
        me = await client.get_me()
        return True
    except:
        return False

async def reconnect(client):
    """Попробовать переподключиться к Telegram"""
    await client.disconnect()
    await client.connect()

async def main():
    client = await setup_client()
    
    # Проверка подключения перед запуском бота
    if not await is_connected(client):
        print("Не удалось подключиться. Попробую переподключиться...")
        await reconnect(client)
    
    handlers = [
        help_handler,
        anime_handler,
        im_handler,
        imstop_handler
    ]

    for handler in handlers:
        client.add_event_handler(handler)

    print("Бот запускается...")

    try:
        await client.run_until_disconnected()
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        time.sleep(5)
        await main()

if __name__ == '__main__':
    asyncio.run(main())

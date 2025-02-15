from telethon import TelegramClient, events, functions, types
import asyncio
import time
import random
import aiohttp
import logging
from datetime import datetime
import pytz

# Задайте свои API ID и API Hash
api_id = 'YOUR_API_ID'  # Замените на ваш API ID
api_hash = 'YOUR_API_HASH'  # Замените на ваш API Hash

# Конфигурация
prefixes = ['.', '/', '!', '-']
logger = logging.getLogger(__name__)

async def setup_client():
    """Настройка и подключение клиента"""
    client = TelegramClient('session_name', api_id, api_hash)

    # Проверка подключения
    await ensure_connected(client)

    return client

async def ensure_connected(client):
    """Проверка подключения клиента"""
    if not client.is_connected():
        try:
            await client.connect()
            print("Успешное подключение!")
        except Exception as e:
            print(f"Ошибка подключения: {e}")
            await client.disconnect()
            await asyncio.sleep(5)  # Ожидание перед повторным подключением
            await ensure_connected(client)

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

_db_name = "MegaMozg"

# Для времени в нике
_time_running = False
_time_timezone = 'Europe/Moscow'

@events.register(events.NewMessage(pattern=f'[{"".join(prefixes)}]time'))
async def time_handler(event):
    """Включить/выключить время в нике"""
    global _time_running
    if _time_running:
        _time_running = False
        await event.edit("<b>Обновление времени в нике остановлено</b>")
    else:
        _time_running = True
        await event.edit("<b>Обновление времени в нике запущено</b>")
        asyncio.create_task(update_nick(event.client))

@events.register(events.NewMessage(pattern=f'[{"".join(prefixes)}]time_msk'))
async def time_msk_handler(event):
    """Переключить время на МСК"""
    global _time_timezone
    _time_timezone = 'Europe/Moscow'
    await event.edit("<b>Время в нике будет отображаться по МСК</b>")

@events.register(events.NewMessage(pattern=f'[{"".join(prefixes)}]time_ekb'))
async def time_ekb_handler(event):
    """Переключить время на ЕКБ"""
    global _time_timezone
    _time_timezone = 'Asia/Yekaterinburg'
    await event.edit("<b>Время в нике будет отображаться по ЕКБ</b>")

@events.register(events.NewMessage(pattern=f'[{"".join(prefixes)}]time_omsk'))
async def time_omsk_handler(event):
    """Переключить время на Омск"""
    global _time_timezone
    _time_timezone = 'Asia/Omsk'
    await event.edit("<b>ура омское время установлено</b>")

@events.register(events.NewMessage(pattern=f'[{"".join(prefixes)}]time_samara'))
async def time_samara_handler(event):
    """Переключить время на Самару"""
    global _time_timezone
    _time_timezone = 'Europe/Samara'
    await event.edit("<b>часовой пояс успешно изменён на Самару!</b>")

async def update_nick(client):
    while _time_running:
        try:
            tz = pytz.timezone(_time_timezone)
            current_time = datetime.now(tz).strftime("%H:%M")
            double_struck_time = to_double_struck(current_time)
            double_struck_bar = "𝕀"

            me = await client.get_me()
            current_nick = me.first_name.split('𝕀')[0].strip()
            new_nick = f"{current_nick} {double_struck_bar} {double_struck_time}"

            await client(functions.account.UpdateProfileRequest(first_name=new_nick))

            now = datetime.now()
            sleep_time = 60 - now.second
            await asyncio.sleep(sleep_time)
        except Exception as e:
            logger.error(f"Nick update error: {e}")
            await asyncio.sleep(60)

def to_double_struck(text):
    """Преобразует текст в шрифт Double Struck"""
    normal = "0123456789:"
    double_struck = "𝟘𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡:"
    translation = str.maketrans(normal, double_struck)
    return text.translate(translation)

db = {}

@events.register(events.NewMessage(pattern=f'[{"".join(prefixes)}]mozg'))
async def mozg_handler(event):
    """Переключить режим дурачка в чате (on/off)"""
    if not event.chat:
        return
    
    chat = event.chat.id
    args = event.raw_text.split(maxsplit=1)[1] if len(event.raw_text.split()) > 1 else ""
    
    if args.lower() not in ["on", "off"]:
        await event.edit("<b>[MegaMozg]</b> Используйте: .mozg on или .mozg off")
        return
        
    if args.lower() == "on":
        chats = db.get(_db_name, {}).get("chats", [])
        chats.append(chat)
        chats = list(set(chats))
        db.setdefault(_db_name, {})["chats"] = chats
        await event.edit("<b>[MegaMozg]</b> Включён")
    else:
        chats = db.get(_db_name, {}).get("chats", [])
        try:
            chats.remove(chat)
        except:
            pass
        chats = list(set(chats))
        db.setdefault(_db_name, {})["chats"] = chats
        await event.edit("<b>[MegaMozg]</b> Выключен")

@events.register(events.NewMessage(pattern=f'[{"".join(prefixes)}]mozgchance'))
async def mozgchance_handler(event):
    """Установить шанс ответа 1 к N"""
    args = event.raw_text.split(maxsplit=1)[1] if len(event.raw_text.split()) > 1 else ""
    if args.isdigit():
        db.setdefault(_db_name, {})["chance"] = int(args)
        await event.edit(f"<b>[MegaMozg]</b> {args}")
    else:
        await event.edit("<b>[MegaMozg]</b> Нужен аргумент")

@events.register(events.NewMessage())
async def mozg_watcher(event):
    if not isinstance(event, types.Message):
        return
    if event.sender_id == (await event.client.get_me()).id or not event.chat:
        return
    if event.chat.id not in db.get(_db_name, {}).get("chats", []):
        return
    ch = db.get(_db_name, {}).get("chance", 0)
    if ch != 0 and random.randint(0, ch) != 0:
        return

    text = event.raw_text
    words = {random.choice(list(filter(lambda x: len(x) >= 3, text.split()))) for _ in ".."}
    msgs = []
    for word in words:
        async for x in event.client.iter_messages(event.chat.id, search=word):
            if x.replies and x.replies.max_id:
                msgs.append(x)
    if not msgs:
        return

    replier = random.choice(msgs)
    sid = replier.id
    eid = replier.replies.max_id
    msgs = []
    async for x in event.client.iter_messages(event.chat.id, ids=list(range(sid + 1, eid + 1))):
        if x and x.reply_to and x.reply_to.reply_to_msg_id == sid:
            msgs.append(x)
    if msgs:
        msg = random.choice(msgs)
        await event.reply(msg)

async def main():
    """Основная функция для запуска бота"""
    client = await setup_client()

    # Подключаем обработчики команд
    handlers = [
        help_handler,
        anime_handler,
        im_handler,
        imstop_handler,
        mozg_handler,
        mozgchance_handler,
        mozg_watcher,
        time_handler,
        time_msk_handler,
        time_ekb_handler,
        time_omsk_handler,
        time_samara_handler
    ]
    
    for handler in handlers:
        client.add_event_handler(handler)

    print("Бот запускается...")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())

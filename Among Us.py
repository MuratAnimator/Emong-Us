import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    CallbackContext,
)
import random
import asyncio

# Настройка логгирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Хранение данных игры
games = {}

async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "Привет! Это мини-игра в стиле Among Us.\n"
        "Создай новую игру или присоединяйся к существующей.\n"
        "Команды:\n"
        "/newgame - создать новую игру\n"
        "/join [ID] - присоединиться к игре\n"
        "/startgame - начать игру (если ты создатель)"
    )

async def new_game(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    game_id = str(random.randint(1000, 9999))
    
    games[game_id] = {
        "creator": chat_id,
        "players": {chat_id: "Not assigned"},
        "status": "waiting"
    }
    
    await update.message.reply_text(
        f"🎮 Игра создана! ID: {game_id}\n"
        f"Другие игроки могут присоединиться через /join {game_id}\n"
        f"Когда все готовы, создатель может запустить игру /startgame"
    )

async def join_game(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    if not context.args:
        await update.message.reply_text("Укажите ID игры: /join [ID]")
        return
    
    game_id = context.args[0]
    if game_id not in games:
        await update.message.reply_text("Игра не найдена! Проверьте ID.")
        return
    
    if games[game_id]["status"] != "waiting":
        await update.message.reply_text("Игра уже началась!")
        return
    
    games[game_id]["players"][chat_id] = "Not assigned"
    await update.message.reply_text(f"Вы присоединились к игре {game_id}! Ожидаем начала...")

async def start_game(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    game_id = None
    
    # Находим игру, где пользователь создатель
    for gid, game in games.items():
        if game["creator"] == chat_id and game["status"] == "waiting":
            game_id = gid
            break
    
    if not game_id:
        await update.message.reply_text("Вы не создавали игру или она уже началась.")
        return
    
    players = list(games[game_id]["players"].keys())
    if len(players) < 2:
        await update.message.reply_text("Нужно минимум 2 игрока!")
        return
    
    # Назначаем роли (1 импостер, остальные - crewmates)
    impostor = random.choice(players)
    for player in players:
        role = "Impostor" if player == impostor else "Crewmate"
        games[game_id]["players"][player] = role
        await context.bot.send_message(
            chat_id=player,
            text=f"🎭 Ваша роль: **{role}**\n\n"
                 f"🔹 Игра началась!\n"
                 f"Impostor должен убивать, Crewmates - выполнять задания."
        )
    
    games[game_id]["status"] = "started"
    await update.message.reply_text("Игра началась! Роли розданы.")

async def button_click(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text=f"Вы выбрали: {query.data}")

def main() -> None:
    # Создаем новый event loop вручную (важно для Pydroid 3)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    application = Application.builder().token("8142036620:AAHUxG7N5lGFalkNJ_efiOQqGxl__SN9tO8").build()  # Замените на свой токен

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("newgame", new_game))
    application.add_handler(CommandHandler("join", join_game))
    application.add_handler(CommandHandler("startgame", start_game))
    application.add_handler(CallbackQueryHandler(button_click))

    application.run_polling()

if __name__ == "__main__":
    main()
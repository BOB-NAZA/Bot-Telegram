import os
import asyncio
import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from database import Database

# Configuration du bot
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Initialisation du bot
logging.basicConfig(level=logging.INFO)
db = Database("bot_data.db")

# Fonction de démarrage
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    keyboard = [
        [InlineKeyboardButton("Configurer", callback_data="config")],
        [InlineKeyboardButton("Voir la publication", callback_data="view_post")],
        [InlineKeyboardButton("Diffuser maintenant", callback_data="send_now")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Bienvenue ! Choisissez une option :", reply_markup=reply_markup)

# Gestion des boutons
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "config":
        await query.message.reply_text("Envoyez le message à publier :")
        context.user_data["config_step"] = "message"
    
    elif query.data == "view_post":
        post = db.get_last_post()
        if post:
            await query.message.reply_text(f"Message actuel :\n{post['message']}")
        else:
            await query.message.reply_text("Aucune publication enregistrée.")

    elif query.data == "send_now":
        post = db.get_last_post()
        if post:
            await context.bot.send_message(chat_id=post["chat_id"], text=post["message"])
            await query.message.reply_text("Message diffusé !")
        else:
            await query.message.reply_text("Aucune publication enregistrée.")

# Enregistrement des paramètres envoyés par l'utilisateur
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    user_text = update.message.text

    if "config_step" in context.user_data and context.user_data["config_step"] == "message":
        db.save_post(chat_id, user_text)
        await update.message.reply_text("Message enregistré !")
        del context.user_data["config_step"]

# Configuration du bot
def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CommandHandler("config", start))
    app.add_handler(CommandHandler("send_now", start))
    app.add_handler(CommandHandler("view_post", start))
    app.add_handler(CommandHandler("set_token", start))
    app.add_handler(CommandHandler("set_group", start))
    app.add_handler(CommandHandler("set_channel", start))
    app.add_handler(CommandHandler("set_image", start))
    app.add_handler(CommandHandler("set_date", start))
    app.add_handler(CommandHandler("set_frequency", start))
    app.add_handler(CommandHandler("schedule_post", start))
    
    app.run_polling()

if __name__ == "__main__":
    main()

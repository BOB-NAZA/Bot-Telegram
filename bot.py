import logging
import sqlite3
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = "TELEGRAM_BOT_TOKEN"

# Connexion à la base de données
conn = sqlite3.connect("bot_data.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS config (id INTEGER PRIMARY KEY, message TEXT, image TEXT, groupes TEXT, frequence INTEGER)''')
cursor.execute("INSERT OR IGNORE INTO config (id, message, image, groupes, frequence) VALUES (1, 'Message par défaut', NULL, '', 1)")
conn.commit()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === MENU PRINCIPAL ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📩 Modifier le message", callback_data="edit_message")],
        [InlineKeyboardButton("🖼️ Changer l'image", callback_data="edit_image")],
        [InlineKeyboardButton("📢 Définir groupes/canaux", callback_data="edit_groups")],
        [InlineKeyboardButton("⏰ Publier X fois par jour", callback_data="edit_frequency")],
        [InlineKeyboardButton("👀 Voir la publication", callback_data="preview")],
        [InlineKeyboardButton("🚀 Diffuser maintenant", callback_data="publish_now")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Bienvenue ! Choisissez une option :", reply_markup=reply_markup)

# === HANDLERS POUR CHAQUE OPTION ===
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "edit_message":
        await query.message.reply_text("Envoyez le nouveau message :")
        context.user_data["edit_mode"] = "message"

    elif query.data == "edit_image":
        await query.message.reply_text("Envoyez une nouvelle image :")
        context.user_data["edit_mode"] = "image"

    elif query.data == "edit_groups":
        await query.message.reply_text("Envoyez les ID des groupes/canaux séparés par des virgules :")
        context.user_data["edit_mode"] = "groups"

    elif query.data == "edit_frequency":
        await query.message.reply_text("Combien de fois par jour voulez-vous publier ? (Ex: 3)")
        context.user_data["edit_mode"] = "frequency"

    elif query.data == "preview":
        cursor.execute("SELECT message, image FROM config WHERE id=1")
        message, image = cursor.fetchone()
        if image:
            await query.message.reply_photo(photo=image, caption=f"📢 Aperçu du message :\n{message}")
        else:
            await query.message.reply_text(f"📢 Aperçu du message :\n{message}")

    elif query.data == "publish_now":
        await publish_message(context)
        await query.message.reply_text("✅ Message diffusé immédiatement !")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "edit_mode" in context.user_data:
        mode = context.user_data["edit_mode"]
        text = update.message.text

        if mode == "message":
            cursor.execute("UPDATE config SET message=? WHERE id=1", (text,))
            await update.message.reply_text("✅ Message mis à jour !")

        elif mode == "groups":
            cursor.execute("UPDATE config SET groupes=? WHERE id=1", (text,))
            await update.message.reply_text("✅ Groupes/canaux mis à jour !")

        elif mode == "frequency":
            try:
                freq = int(text)
                cursor.execute("UPDATE config SET frequence=? WHERE id=1", (freq,))
                await update.message.reply_text("✅ Fréquence mise à jour !")
            except ValueError:
                await update.message.reply_text("⚠️ Veuillez entrer un nombre valide.")

        conn.commit()
        context.user_data.pop("edit_mode")

async def image_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "edit_mode" in context.user_data and context.user_data["edit_mode"] == "image":
        file = await update.message.photo[-1].get_file()
        image_url = file.file_path
        cursor.execute("UPDATE config SET image=? WHERE id=1", (image_url,))
        conn.commit()
        await update.message.reply_text("✅ Image mise à jour !")
        context.user_data.pop("edit_mode")

async def publish_message(context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT message, image, groupes FROM config WHERE id=1")
    message, image, groupes = cursor.fetchone()
    group_list = groupes.split(',')

    for group in group_list:
        try:
            if image:
                await context.bot.send_photo(chat_id=group.strip(), photo=image, caption=message)
            else:
                await context.bot.send_message(chat_id=group.strip(), text=message)
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi : {e}")

# === LANCEMENT DU BOT ===
app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
app.add_handler(MessageHandler(filters.PHOTO, image_handler))

print("✅ Bot en cours d'exécution...")
app.run_polling()

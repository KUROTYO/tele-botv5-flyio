
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from deep_translator import GoogleTranslator
from flask import Flask
from threading import Thread

# Flask setup for Fly.io keep-alive
app = Flask(__name__)
@app.route('/')
def home(): return "I'm alive!"
def run_web(): app.run(host='0.0.0.0', port=5000)
def keep_alive(): Thread(target=run_web).start()

# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot Token and Channel
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_USERNAME = "Traveler_01"

# Expanded language support
LANGUAGES = {
    'afrikaans': 'af', 'arabic': 'ar', 'azerbaijani': 'az', 'bulgarian': 'bg',
    'chinese': 'zh-CN', 'czech': 'cs', 'danish': 'da', 'dutch': 'nl',
    'english': 'en', 'finnish': 'fi', 'french': 'fr', 'georgian': 'ka',
    'german': 'de', 'greek': 'el', 'gujarati': 'gu', 'hebrew': 'he',
    'hindi': 'hi', 'hungarian': 'hu', 'indonesian': 'id', 'italian': 'it',
    'japanese': 'ja', 'korean': 'ko', 'malay': 'ms', 'nepali': 'ne',
    'norwegian': 'no', 'persian': 'fa', 'polish': 'pl', 'portuguese': 'pt',
    'punjabi': 'pa', 'romanian': 'ro', 'russian': 'ru', 'slovak': 'sk',
    'slovenian': 'sl', 'spanish': 'es', 'swahili': 'sw', 'swedish': 'sv',
    'tamil': 'ta', 'telugu': 'te', 'thai': 'th', 'turkish': 'tr',
    'ukrainian': 'uk', 'urdu': 'ur', 'vietnamese': 'vi'
}

user_languages = {}

def create_language_keyboard():
    keyboard = []
    languages_list = list(LANGUAGES.keys())
    for i in range(0, len(languages_list), 2):
        row = []
        for j in range(2):
            if i + j < len(languages_list):
                lang = languages_list[i + j]
                row.append(InlineKeyboardButton(lang.capitalize(), callback_data=f"lang_{lang}"))
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

async def check_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await check_subscription(user.id, context):
        keyboard = [[InlineKeyboardButton("Subscribe to Channel", url=f"https://t.me/{CHANNEL_USERNAME}")],
                    [InlineKeyboardButton("Check Subscription", callback_data="check_subscription")]]
        await update.message.reply_text(
            f"Welcome {user.mention_html()}! 🌍\n\n"
            f"To use this translation bot, please subscribe to our channel first:\n"
            f"@{CHANNEL_USERNAME}\n\nAfter subscribing, click 'Check Subscription' below.",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    await update.message.reply_text(
        f"Welcome {user.mention_html()}! 🌍\n\n"
        f"📝 Send a text\n🌐 Choose a language\n✨ Get translation!",
        parse_mode='HTML',
        reply_markup=create_language_keyboard()
    )

async def languages_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🌐 Supported Languages:\n" + ", ".join(LANGUAGES.keys()))

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send any text. Then click a language to translate it.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_languages[update.effective_user.id] = update.message.text
    await update.message.reply_text("Choose a target language:", reply_markup=create_language_keyboard())

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if query.data == "check_subscription":
        if await check_subscription(user_id, context):
            await query.edit_message_text("✅ Subscription confirmed! Send a message to translate.")
        else:
            await query.edit_message_text("❌ You're still not subscribed.")
        return
    if query.data.startswith("lang_"):
        lang = query.data.replace("lang_", "")
        if user_id not in user_languages:
            await query.edit_message_text("❗ Send a text first.")
            return
        original = user_languages[user_id]
        translated = GoogleTranslator(source='auto', target=LANGUAGES[lang]).translate(original)
        await query.edit_message_text(f"📝 Original: {original}\n🌍 {lang.capitalize()}: {translated}")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Update error:", exc_info=context.error)

def main():
    keep_alive()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("languages", languages_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_error_handler(error_handler)
    app.run_polling()

if __name__ == '__main__':
    main()

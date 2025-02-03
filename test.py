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
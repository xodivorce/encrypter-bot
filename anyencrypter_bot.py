import os
import random
import time
import shutil
from PIL import Image, ImageDraw, ImageFont
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (ApplicationBuilder, CommandHandler, MessageHandler, 
                          CallbackContext, CallbackQueryHandler, filters, 
                          ContextTypes)

# Replace with your actual bot token
TOKEN = "7871296394:AAEkoRutVIb6In26pUxXIaopR1YnaEhlRYw"
ADMIN_ID = 1350528516 # Main Admin ID
PASSWORD = "911" 

sub_admins = []  # List to hold sub-admin IDs
all_users = set()  # Set to store all unique user IDs
pending_broadcasts = {} # Store pending broadcasts with user_id as key and list of approvers as value
cooldown_users = {}# Store the cooldown state
admin_requested_delete = {}# Store the /pass state
# Function to generate a 6-digit token
def generate_token():
    return ''.join(random.choices('0123456789', k=6))

# Function to write the token and filename on an image
def write_token_on_image(token, file_name):
    """Write the token and file name on an image."""
    image_path = "assets/token/token.jpg"
    img = Image.open(image_path).convert("RGB")  # Convert to RGB mode
    draw = ImageDraw.Draw(img)

    # Try loading the desired font, fall back to default if not available
    try:
        font = ImageFont.truetype("arial.ttf", 24)  # Use a larger font
    except IOError:
        font = ImageFont.load_default()  # Fallback to default font

    # Get image size and calculate the text bounding box
    image_width, image_height = img.size
    text = f"File: {file_name}\nToken: {token}"

    # Anti-aliasing with better spacing for clearer text
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]


    # Calculate position to center the text
    x = (image_width - text_width) / 2
    y = (image_height - text_height) / 2

     # Define text color and high contrast background color
    draw.rectangle([x - 10, y - 10, x + text_width + 10, y + text_height + 10], fill="white")  # Background
    draw.text((x, y), text, font=font, fill="black")  # Sharp black text on a white background

    # Save the modified image
    token_image_path = "assets/token/token_with_code.jpg"
    img.save(token_image_path)
    print(f"Token '{token}' and file name '{file_name}' written to image and saved as '{token_image_path}'.")

# Function to save the file and generate token
async def save_file(update: Update, context):
    file_type = context.user_data.get('file_type')

    # Get user ID
    user_id = update.effective_user.id

    # Ensure user-specific folders exist for each file type
    base_folder = f"assets/{user_id}"
    os.makedirs(f"{base_folder}/image", exist_ok=True)
    os.makedirs(f"{base_folder}/audio", exist_ok=True)
    os.makedirs(f"{base_folder}/video", exist_ok=True)
    os.makedirs(f"{base_folder}/document", exist_ok=True)

    # Get the file object
    document = update.message.document
    if document is None:
        await update.message.reply_text("No file detected. Please send a file.")
        return

    file_extension = document.file_name.split('.')[-1].lower()

    # Check file type and save in the correct user-specific folder
    if file_type == 'audio' and file_extension in ['mp3', 'mp4', 'wav', 'aac']:
        folder = f"{base_folder}/audio/"
    elif file_type == 'img' and file_extension in ['jpg', 'jpeg', 'png', 'webp', 'ico']:
        folder = f"{base_folder}/image/"
    elif file_type == 'doc' and file_extension in ['pdf', 'docx', 'txt', 'zip', 'tar', '7z', 'apk', 'xapk']:
        folder = f"{base_folder}/document/"
    elif file_type == 'video' and file_extension in ['mp3','mp4', 'mkv', 'mov', 'avi']:
        folder = f"{base_folder}/video/"
    else:
        await update.message.reply_text("Unsupported file type or no file detected. Please follow the steps and try again.")
        return

    # Create a unique file name to prevent overwriting
    file_path = os.path.join(folder, document.file_name)
    base_file_name, ext = os.path.splitext(document.file_name)
    counter = 1

    while os.path.exists(file_path):
        file_path = os.path.join(folder, f"{base_file_name} ({counter}){ext}")
        counter += 1

    # Download the file to the specified path
    file = await document.get_file()
    await file.download_to_drive(file_path)

    # Generate a token
    token = generate_token()

    # Simulate processing time
    await update.message.reply_text("Processing your file, please wait...")
    time.sleep(2)  # Simulating a 2-second processing time

    # Generate token image with file name
    write_token_on_image(token, document.file_name)

    # Save token and file name to a global text file in assets/logs
    # Save token and file name to a global text file in assets/logs
    user_log_path = f"assets/logs/{user_id}_token_info.txt"
    with open(user_log_path, "a") as f:
        f.write(f"{document.file_name}: {token}\n")



    # Send the token image to the user and a clickable token message
    await update.message.reply_photo(open("assets/token/token_with_code.jpg", "rb"), caption=f"Your token is: `{token}`", parse_mode='Markdown')

    print(f"File '{document.file_name}' saved at {file_path} with token: {token}")

    


# Command to show available commands
async def help_command(update: Update, context):
    user_id = update.effective_user.id
    admin_commands = (
        "/rules - View the rules.\n"
        "/logs - View your logs.\n"
        "/idlogs - View users logs.\n"
        "/clear - Clear your logs and associated files.\n"
        "/add <user_id> - Add a sub-admin by user ID.\n"
        "/remove <user_id> - Remove a sub-admin by user ID.\n"
        "/delete_user <user_id> - Delete specific user's logs and data.\n"
        "/delete_all - Delete all logs and data.\n"
        "/view_id - View your user ID and Sub-admin IDs.\n"
        "/broadcast - broadcast a message to users.\n"
    )

    if user_id == ADMIN_ID:
        commands = (
            "/img for images.\n"
            "/doc for documents.\n"
            "/video for video files.\n"
            "/audio for audio files (*currently unavailable!).\n"
            "/decrypt <6-digit-code> - decrypt & get the file.\n\n"
            "Administration commands:\n"
            f"{admin_commands}"
        )
    elif user_id in sub_admins:
        commands = (
            "/img for images.\n"
            "/doc for documents.\n"
            "/video for video files.\n"
            "/audio for audio files (*currently unavailable!).\n"
            "/decrypt <6-digit-code> - decrypt & get the file.\n\n"
            "Administration commands:\n"
            "/rules - View the rules.\n"
            "/logs - View your logs.\n"
            "/idlogs - View users logs.\n"
            "/clear - Clear your logs and associated files.\n"
            "/delete_user <user_id> - Delete specific user's logs and data.\n"
            "/view_id - View your user ID and Sub-admin IDs.\n"
            "/broadcast - broadcast a message to users.\n"
        )
    else:
        commands = (
            "/img for images\n"
            "/doc for documents\n"
            "/video for video files\n"
            "/audio for audio files (*currently unavailable!).\n"
            "/decrypt <6-digit-code> - decrypt & get the file.\n\n"
            "Privacy commands:\n"
            "/rules - View the rules.\n"
            "/logs - View your logs.\n"
            "/clear - Clear your logs and associated files.\n"
        )

    await update.message.reply_text(f"What would you like to encrypt? Please choose from the following commands:\n{commands}")

# Load sub-admins from file
def load_sub_admins():
    global sub_admins
    if os.path.exists("assets/admin/sub_admins.txt"):
        with open("assets/admin/sub_admins.txt", "r") as f:
            sub_admins = [int(line.strip()) for line in f.readlines() if line.strip().isdigit()]

# Save sub-admins to file
def save_sub_admins():
    with open("assets/admin/sub_admins.txt", "w") as f:
        for admin_id in sub_admins:
            f.write(f"{admin_id}\n")

# Function to send a message to all sub-admins
async def notify_sub_admins(message: str):
    for sub_admin_id in sub_admins:
        try:
            await app.bot.send_message(chat_id=sub_admin_id, text=message)
        except Exception as e:
            print(f"Failed to send message to Sub-admin ID {sub_admin_id}: {e}")

# Command to add a sub-admin
async def add_sub_admin(update: Update, context):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("You are not authorized to add Sub-admins.")
        return

    if len(context.args) == 0:
        await update.message.reply_text("Please provide a user ID to add as a Sub-admin.")
        return

    try:
        new_sub_admin_id = int(context.args[0])
        if new_sub_admin_id not in sub_admins:
            sub_admins.append(new_sub_admin_id)
            save_sub_admins()  # Save the new sub-admin list
            await update.message.reply_text(f"User ID {new_sub_admin_id} added as a Sub-admin.", parse_mode='Markdown')
            await notify_sub_admins(f"User ID {new_sub_admin_id} has been added as a Sub-admin.", parse_mode='Markdown')
        else:
            await update.message.reply_text("This user is already a Sub-admin.")
    except ValueError:
        await update.message.reply_text("Invalid user ID format. Please provide a valid user ID.")

# Command to remove a sub-admin
async def remove_sub_admin(update: Update, context):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("You are not authorized to remove Sub-admins.")
        return

    if len(context.args) == 0:
        await update.message.reply_text("Please provide a user ID to remove as a Sub-admin.")
        return

    try:
        sub_admin_id_to_remove = int(context.args[0])
        if sub_admin_id_to_remove in sub_admins:
            sub_admins.remove(sub_admin_id_to_remove)
            save_sub_admins()  # Save the updated sub-admin list
            await update.message.reply_text(f"User ID {sub_admin_id_to_remove} has been removed as a Sub-admin.", parse_mode='Markdown')
            await notify_sub_admins(f"User ID {sub_admin_id_to_remove} has been removed as a Sub-admin.", parse_mode='Markdown')
        else:
            await update.message.reply_text("This user is not a Sub-admin.")
    except ValueError:
        await update.message.reply_text("Invalid user ID format. Please provide a valid user ID.")

# Command to view logs
async def view_logs(update: Update, context):
    user_log_path = f"assets/logs/{update.effective_user.id}_token_info.txt"
    if os.path.exists(user_log_path):
        with open(user_log_path, "r") as f:
            logs = f.read()
        await update.message.reply_text(f"Your logs:\n{logs}", parse_mode='Markdown')
    else:
        await update.message.reply_text("No logs found for your user ID.")


# Decrypt
async def decrypt(update: Update, context):
    if len(context.args) == 0:
        await update.message.reply_text("Usage: /decrypt <6-digit-code>\nPlease provide a 6-digit code.")
        return

    token = context.args[0]

    # Validate token format
    if not token.isdigit() or len(token) != 6:
        await update.message.reply_text("Invalid token or format. Please provide a valid 6-digit code.")
        return

    # Search for the token in the global logs
    found = False
    for user_log_file in os.listdir("assets/logs"):  # Check all log files in assets/logs
        user_log_path = os.path.join("assets/logs", user_log_file)

        with open(user_log_path, "r") as f:
            lines = f.readlines()
            for line in lines:
                # Split the line and strip any excess whitespace
                file_name, file_token = line.strip().split(": ")
                file_token = file_token.strip()

                if file_token == token:
                    found = True
                    # Extract the user_id from the log file name
                    user_id = user_log_file.split("_")[0]

                    # Check user-specific folders to locate the file
                    for folder in ['image', 'audio', 'video', 'document']:
                        file_path = os.path.join(f"assets/{user_id}/{folder}", file_name)
                        if os.path.exists(file_path):
                            # Send the file to the user who requested it
                            await update.message.reply_text("File found. Sending the file to you now.")
                            await update.message.reply_document(open(file_path, 'rb'))
                            return

    if not found:
        await update.message.reply_text("Invalid code or file not found. Please try again.")



# Command to view logs of a specific user
async def idlogs(update: Update, context):
    user_id = update.effective_user.id

    # Check if the user is admin or sub-admin
    if user_id != ADMIN_ID and user_id not in sub_admins:
        await update.message.reply_text("You are not authorized to view logs for other users.")
        return

    if len(context.args) == 0:
        await update.message.reply_text("Usage: /idlogs <userid>\nPlease provide a user ID to view their logs.")
        return

    try:
        target_user_id = int(context.args[0])
        user_log_path = f"assets/logs/{target_user_id}_token_info.txt"

        if os.path.exists(user_log_path):
            with open(user_log_path, "r") as f:
                logs = f.read()
            await update.message.reply_text(f"Logs for user ID {target_user_id}:\n{logs}")
        else:
            await update.message.reply_text("No logs found for this user ID.")
    except ValueError:
        await update.message.reply_text("Invalid user ID format. Please provide a valid user ID.")


# Command to inform the user about how to clear their logs
async def clear_user_logs_and_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(
        f"Your User ID: {user_id}\n"
        f"To delete your logs and files, please send the command:\n"
        f"`/pass {user_id}/anyencrypter`", 
        parse_mode='MarkdownV2'  # Enable Markdown for formatting
    )

# Command to handle the deletion process
async def handle_pass_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command_args = context.args

    # Check if the command starts with /pass and has only one argument (the user ID)
    if len(command_args) != 1 or '/' not in command_args[0]:
        await update.message.reply_text("Invalid command format. Please use /pass <user_id>/anyencrypter to delete.")
        return

    # Split the user_id and the keyword
    user_id, keyword = command_args[0].split('/')

    # Ensure the keyword matches "anyencrypter"
    if keyword != "anyencrypter":
        await update.message.reply_text("Invalid command. Please use /pass <user_id>/anyencrypter to delete.")
        return

    # Get the ID of the user sending the command
    sending_user_id = update.effective_user.id

    # Check if the provided user ID matches the sending user's ID
    if str(sending_user_id) != user_id:
        await update.message.reply_text("User ID does not match. Please use the correct User ID to delete.")
        return

    # Define the paths for the user folder and log file
    user_log_path = f"assets/logs/{user_id}_token_info.txt"  # Log file path
    user_folder_path = f"assets/{user_id}/"  # User folder path

    # Check if the user folder or log file exists
    if not os.path.exists(user_folder_path) and not os.path.exists(user_log_path):
        await update.message.reply_text("Your logs and all files are already cleared.")
        return

    # If the user folder exists, delete the files within it
    if os.path.exists(user_folder_path):
        for folder in ['image', 'audio', 'video', 'document']:
            folder_path = os.path.join(user_folder_path, folder)
            if os.path.exists(folder_path):
                for filename in os.listdir(folder_path):
                    file_path = os.path.join(folder_path, filename)
                    os.remove(file_path)  # Remove each file
                    

                # Remove folder if it is empty
                if not os.listdir(folder_path):
                    os.rmdir(folder_path)
                    
        # Delete the user's main folder if it is empty
        if not os.listdir(user_folder_path):
            os.rmdir(user_folder_path)
            
    # Delete the log file if it exists
    if os.path.exists(user_log_path):
        os.remove(user_log_path)
       
    await update.message.reply_text("Your logs and all files you sent to the bot have been cleared.")





async def delete_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID and user_id not in sub_admins:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Usage: /delete_user <user_id>")
        return

    target_user_id = context.args[0]
    user_folder = os.path.join("assets", target_user_id)
    logs_folder = "assets/logs"
    user_log_file = f"{target_user_id}_token_info.txt"
    user_log_path = os.path.join(logs_folder, user_log_file)

    # Delete user folder if it exists
    if os.path.isdir(user_folder):
        shutil.rmtree(user_folder)
        await update.message.reply_text(f"Deleted user folder: {user_folder}")
    else:
        await update.message.reply_text(f"No folder found for user ID: {target_user_id}")

    # Delete user log file if it exists
    if os.path.exists(user_log_path):
        os.remove(user_log_path)
        await update.message.reply_text(f"Deleted log file: {user_log_path}")
    else:
        await update.message.reply_text(f"No log or file found for user ID: {target_user_id}")


  

admin_requested_delete = {}

async def delete_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id != ADMIN_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    await update.message.reply_text("Please send the password using /mode <password>.")
    admin_requested_delete[user_id] = True

async def check_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id != ADMIN_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    message_text = update.message.text

    # Debugging line
    print(f"Received command from user_id: {user_id}, message: {message_text}")

    if not message_text.startswith('/mode '):
        await update.message.reply_text("Invalid command format. Please use /mode <password>.")
        return

    if user_id not in admin_requested_delete or not admin_requested_delete[user_id]:
        await update.message.reply_text("Invalid command. Please use /delete_all first.")
        return

    input_password = message_text.split(" ")[1] if len(message_text.split(" ")) > 1 else ""

    if input_password == PASSWORD:
        await delete_all_files(update)
        admin_requested_delete[user_id] = False
    else:
        await update.message.reply_text("Incorrect password. Please try again.")

async def delete_all_files(update: Update):
    # Path to the assets folder
    assets_folder = "assets"
    
    # Loop through all folders in 'assets' and delete everything except 'token', 'admin', and 'logs'
    for folder in os.listdir(assets_folder):
        folder_path = os.path.join(assets_folder, folder)
        if os.path.isdir(folder_path) and folder not in ["token", "admin", "logs"]:
            shutil.rmtree(folder_path)  # Delete the entire folder
            print(f"Deleted folder: {folder_path}")
    
    # Clear files inside 'assets/logs', but keep the folder
    logs_folder = os.path.join(assets_folder, "logs")
    if os.path.exists(logs_folder):
        for filename in os.listdir(logs_folder):
            file_path = os.path.join(logs_folder, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)  # Delete each file
                print(f"Deleted log file: {file_path}")
    
    await update.message.reply_text("All folders and log files have been deleted, except for 'token', 'admin', and the 'logs' folder.")







# Command to view user IDs (restricted to admin and sub-admins)
async def view_ids(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    # Check if the user is admin or sub-admin
    if user_id != ADMIN_ID and user_id not in sub_admins:
        await update.message.reply_text("You are not authorized to view user IDs.")
        return

    # Read all user IDs from all_users.txt
    user_log_path = "assets/admin/all_users.txt"
    if not os.path.exists(user_log_path):
        await update.message.reply_text("No users found.")
        return
    
    with open(user_log_path, "r") as f:
        all_users_from_file = set(f.read().splitlines())  # Use a set to ensure uniqueness

    # Exclude admin and sub-admin IDs
    ids_to_display = all_users_from_file - {str(ADMIN_ID)} - set(map(str, sub_admins))

    # Create a numbered list of filtered user IDs
    ids = f"Your User ID: `{user_id}`\n\n"
    
    # Check if there are sub-admins and add them to the message
    if sub_admins:
        ids += "Sub-admin IDs:\n"
        for i, sub_admin_id in enumerate(sub_admins, 1):
            ids += f"{i}. `{sub_admin_id}`\n"
    else:
        ids += "No sub-admins found.\n"

    # Display the filtered list of user IDs
    if ids_to_display:
        ids += "\nAll User IDs:\n"
        for i, user in enumerate(ids_to_display, 1):
            ids += f"{i}. `{user}`\n"
    else:
        ids += "\nNo users found.\n"

    # Send the formatted message
    await update.message.reply_text(ids, parse_mode="Markdown")


# Command to handle when the user starts interacting with the bot
async def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name or "User"  # Get first name or fallback to "User"

    # Path to all_users.txt
    user_log_path = "assets/admin/all_users.txt"
    
    # Ensure the user ID is not already in the file
    if os.path.exists(user_log_path):
        with open(user_log_path, "r") as f:
            existing_user_ids = set(f.read().splitlines())  # Load existing user IDs as a set for uniqueness
    else:
        existing_user_ids = set()

    # Add the user ID to the file only if it's not already saved
    if str(user_id) not in existing_user_ids:
        with open(user_log_path, "a") as f:
            f.write(f"{user_id}\n")

    # Welcome message with the user's first name
    welcome_message = f"Welcome, {first_name}!\nTry to run this command: /help\nReview the rules: /rules\nSupport: hey@xodivorce.in"
    await update.message.reply_text(welcome_message)

    
# Command to show the bot's rules
async def rules(update: Update, context):
    rules_text = (
        "Welcome to @anyencrypter_bot! Please adhere to the following rules:\n\n"
        "1. Send only supported file formats.\n"
        "2. File size must not exceed 20MB.\n"
        "3. Avoid spamming repeated requests.\n"
        "4. Follow commands as instructed.\n"
        "5. Files are deleted after 30 days. Contact hey@xodivorce.in for paid plans to retain them.\n"
        "6. The bot operates daily from 12 PM to 3 AM IST.\n"
        "7. If the bot is offline, send the command and it will process while active.\n"
        "8. For issues, contact: hey@xodivorce.in.\n"
    )
    await update.message.reply_text(rules_text)



# Function to handle broadcast requests
async def broadcast(update: Update, context: CallbackContext):
    """Handle the /broadcast command for admin and sub-admins."""
    user_id = update.effective_user.id
    message = ' '.join(context.args)

    if not message:
        await update.message.reply_text("Usage: /broadcast <your message>\nPlease provide a message to broadcast.", parse_mode='Markdown')
        return

    if user_id == ADMIN_ID:
        # Admin sends the broadcast directly
        await send_broadcast(context, message)
        await update.message.reply_text("Broadcast sent successfully.")
    elif user_id in sub_admins:
        # Sub-admin sends a request, show approval buttons to the admin
        pending_broadcasts[user_id] = message

        # Create inline buttons for Approve/Reject
        buttons = [
            [InlineKeyboardButton("Approve", callback_data=f"approve:{user_id}"),
             InlineKeyboardButton("Reject", callback_data=f"reject:{user_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)

        await update.message.reply_text("Your broadcast request has been sent to @xodivorce(admin) for approval.", parse_mode='Markdown')
        admin_message = f"Sub-admin {user_id} has requested to broadcast the following message:\n\n{message}\n\nApprove or Reject the request:"
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_message, reply_markup=reply_markup)
    else:
        await update.message.reply_text("You do not have permission to broadcast messages.")

# Callback query handler for processing the broadcast approval/rejection
async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id  # Admin or sub-admin user ID

    # Ensure the bot acknowledges the callback query
    await query.answer()

    # Check if the callback query data matches "approve" or "reject"
    action, sub_admin_id = query.data.split(':')  # Split the callback data, which is 'approve:<sub_admin_id>' or 'reject:<sub_admin_id>'
    sub_admin_id = int(sub_admin_id)

    if action == 'approve':
        # Approve the broadcast
        if sub_admin_id in pending_broadcasts:
            # Get the message from pending broadcasts
            message = pending_broadcasts[sub_admin_id]

            # Broadcast the message to all users
            await send_broadcast(context, message)

            # Inform the sub-admin about the approval
            await context.bot.send_message(chat_id=sub_admin_id, text="Your broadcast request has been approved and sent to all users.", parse_mode='Markdown')

            # Remove the broadcast request from the pending list
            del pending_broadcasts[sub_admin_id]

            # Update the message for the admin
            await query.edit_message_text(f"Broadcast from sub-admin {sub_admin_id} approved and sent to all users.", parse_mode='Markdown')
        else:
            await query.edit_message_text(f"No pending broadcast request found for sub-admin {sub_admin_id}.", parse_mode='Markdown')

    elif action == 'reject':
        # Reject the broadcast
        if sub_admin_id in pending_broadcasts:
            # Inform the sub-admin about the rejection
            await context.bot.send_message(chat_id=sub_admin_id, text="Your broadcast request has been rejected.", parse_mode='Markdown')

            # Remove the broadcast request from the pending list
            del pending_broadcasts[sub_admin_id]

            # Update the message for the admin
            await query.edit_message_text(f"Broadcast from sub-admin {sub_admin_id} rejected.", parse_mode='Markdown')
        else:
            await query.edit_message_text(f"No pending broadcast request found for sub-admin {sub_admin_id}.", parse_mode='Markdown')

# Function to send broadcast to all users
async def send_broadcast(context: CallbackContext, message: str):
    """Send a broadcast message to all users listed in the logs."""
    user_ids = []
    try:
        # Load user IDs from the log file
        with open('assets/admin/all_users.txt', 'r') as file:
            user_ids = [line.strip() for line in file.readlines()]
    except FileNotFoundError:
        return

    # Send the message to each user
    for user_id in user_ids:
        try:
            await context.bot.send_message(chat_id=user_id, text=message)
        except Exception:
            pass  # Continue even if some messages fail to send

# Main function to start the bot
if __name__ == "__main__":
    load_sub_admins()
    app = ApplicationBuilder().token(TOKEN).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CommandHandler("help", help_command))  # Add help command
    app.add_handler(CommandHandler("rules", rules))  # Add rules command
    app.add_handler(CommandHandler("broadcast", broadcast)) # Handle approve/reject buttons
    app.add_handler(CommandHandler("img", lambda update, context: context.user_data.__setitem__('file_type', 'img') or update.message.reply_text("Please send the image file:\n1. Ping (📎) icon.\n2. Select 'File'.\n3. Send the img file (.png, .jpg, .webp, .jpeg, .ico).\n4. Image must be under 20mb (lesser the file size, faster the encrypt).")))
    app.add_handler(CommandHandler("audio", lambda update, context: context.user_data.__setitem__('file_type', 'audio') or update.message.reply_text("Please send the audio file.\n1. Ping (📎) icon.\n2. Select 'File'.\n3. Send the audio file (.mp3, .mp4, .wav, .mov, .aac).\n4. Doc must be under 20mb (lesser the file size, faster the encrypt).")))
    app.add_handler(CommandHandler("doc", lambda update, context: context.user_data.__setitem__('file_type', 'doc') or update.message.reply_text("Please send the doc file.\n1. Ping (📎) icon.\n2. Select 'File'.\n3. Send the doc file (.pdf, .docx, .txt, .zip, .tar, .7z).\n4. Doc must be under 20mb (lesser the file size, faster the encrypt).")))
    app.add_handler(CommandHandler("video", lambda update, context: context.user_data.__setitem__('file_type', 'video') or update.message.reply_text("Please send the video file.\n1. Ping (📎) icon.\n2. Select 'File'.\n3. Send the video file (.mp3, .mp4, .mvk, .avi).\n4. Video must be under 20mb (lesser the file size, faster the encrypt).")))
    app.add_handler(CommandHandler("decrypt", decrypt))
    app.add_handler(CommandHandler("add", add_sub_admin))
    app.add_handler(CommandHandler("remove", remove_sub_admin))
    app.add_handler(CommandHandler("logs", view_logs))
    app.add_handler(CommandHandler("idlogs", idlogs))
    app.add_handler(CommandHandler("clear", clear_user_logs_and_files))
    app.add_handler(CommandHandler("pass", handle_pass_command))
    app.add_handler(CommandHandler('delete_user', delete_user))
    app.add_handler(CommandHandler("delete_all", delete_all))
    app.add_handler(CommandHandler("mode", check_password))
    app.add_handler(CommandHandler('pass', check_password))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CommandHandler("view_id", view_ids))
    app.add_handler(MessageHandler(filters.Document.ALL, save_file))
    

    app.run_polling()
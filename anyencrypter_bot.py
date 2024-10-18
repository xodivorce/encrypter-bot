import os
import random
import time
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext

#load .env 
load_dotenv()

# Replace with your actual bot token
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 1350528516 # Main Admin ID

sub_admins = []  # List to hold sub-admin IDs
all_users = set()  # Set to store all unique user IDs
pending_broadcasts = {} # Store pending broadcasts with user_id as key and list of approvers as value
pending_approvals = {}
broadcast_requests = {}
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

    # Ensure the assets and subfolders exist
    os.makedirs("assets/image", exist_ok=True)
    os.makedirs("assets/audio", exist_ok=True)
    os.makedirs("assets/video", exist_ok=True)
    os.makedirs("assets/document", exist_ok=True)

    # Get the file object
    document = update.message.document
    if document is None:
        await update.message.reply_text("No file detected. Please send a file.")
        return

    file_extension = document.file_name.split('.')[-1].lower()

    # Check file type and save in the correct folder
    if file_type == 'audio' and file_extension in ['mp3', 'mp4', 'wav', 'aac']:
        folder = "assets/audio/"
    elif file_type == 'img' and file_extension in ['jpg', 'jpeg', 'png', 'webp', 'ico']:
        folder = "assets/image/"
    elif file_type == 'doc' and file_extension in ['pdf', 'docx', 'txt', 'zip', 'tar', '7z']:
        folder = "assets/document/"
    elif file_type == 'video' and file_extension in ['mp3','mp4', 'mkv', 'mov', 'avi']:
        folder = "assets/video/"
    else:
        await update.message.reply_text("Unsupported file type or no file detected. Please try again.")
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

    # Save token and file name to a text file (user-specific)
    user_log_path = f"assets/logs/{update.effective_user.id}_token_info.txt"
    with open(user_log_path, "a") as f:
        f.write(f"{document.file_name}: {token}\n")

    # Send the token image to the user and a clickable token message
    await update.message.reply_photo(open("assets/token/token_with_code.jpg", "rb"), caption=f"Your token is: `{token}`", parse_mode='Markdown')

    print(f"File '{document.file_name}' saved at {file_path} with token: {token}")
    

# Command to ask the user what they want to encrypt
async def start(update: Update, context):
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name or "User"  # Get first name or fallback to "User"
    all_users.add(user_id)  # Add user to the set of all users

    # Welcome message with the user's first name
    welcome_message = f"Welcome, {first_name}!\nTry to run this command: /help\nSupport: hey@xodivorce.in"
    await update.message.reply_text(welcome_message)

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
        "/delete_user_logs <user_id> - Delete specific user's logs and data.\n"
        "/delete_all_logs - Delete all logs and data.\n"
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
            "/delete_user_logs <user_id> - Delete specific user's logs and data.\n"
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
    if os.path.exists("assets/logs/sub_admins.txt"):
        with open("assets/logs/sub_admins.txt", "r") as f:
            sub_admins = [int(line.strip()) for line in f.readlines() if line.strip().isdigit()]

# Save sub-admins to file
def save_sub_admins():
    with open("assets/logs/sub_admins.txt", "w") as f:
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
            await update.message.reply_text(f"User ID {new_sub_admin_id} added as a Sub-admin.")
            await notify_sub_admins(f"User ID {new_sub_admin_id} has been added as a Sub-admin.")
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
            await update.message.reply_text(f"User ID {sub_admin_id_to_remove} has been removed as a Sub-admin.")
            await notify_sub_admins(f"User ID {sub_admin_id_to_remove} has been removed as a Sub-admin.")
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
        await update.message.reply_text(f"Your logs:\n{logs}")
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
        await update.message.reply_text("Invalid token format. Please provide a valid 6-digit code.")
        return

    # Search for the token in all user logs
    found = False
    for user_id in os.listdir("assets/logs"):  # Check all user log files
        user_log_path = f"assets/logs/{user_id}"
        
        # Skip any non-txt files (e.g., directories or unrelated files)
        if not user_log_path.endswith("_token_info.txt"):
            continue
        
        with open(user_log_path, "r") as f:
            lines = f.readlines()
            for line in lines:
                # Split the line and strip any excess whitespace
                file_name, file_token = line.strip().split(": ")
                file_token = file_token.strip()

                if file_token == token:
                    # File associated with the token is found
                    found = True

                    # Check all folders to locate the file
                    for folder in ['assets/image', 'assets/audio', 'assets/video', 'assets/document']:
                        file_path = os.path.join(folder, file_name)
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


# Command to clear user logs and files
async def clear_user_logs_and_files(update: Update, context):
    user_log_path = f"assets/logs/{update.effective_user.id}_token_info.txt"
    user_files_folder = f"assets/user_files/{update.effective_user.id}/"
    
    # Delete log file
    if os.path.exists(user_log_path):
        os.remove(user_log_path)
    
    # Delete user-specific folder if exists
    if os.path.exists(user_files_folder):
        os.rmdir(user_files_folder)
    
    await update.message.reply_text("Your logs and associated files have been cleared.")

# Command to delete specific user's logs
async def delete_user_logs(update: Update, context):
    user_id_to_delete = int(context.args[0]) if context.args else None
    if user_id_to_delete is None:
        await update.message.reply_text("Usage: /delete_user_logs <userid>\nPlease provide a user ID to delete their logs.")
        return

    if user_id_to_delete == ADMIN_ID or user_id_to_delete in sub_admins:
        await update.message.reply_text("You cannot delete logs for the admin or sub-admins.")
        return

    user_log_path = f"assets/logs/{user_id_to_delete}_token_info.txt"
    if os.path.exists(user_log_path):
        os.remove(user_log_path)
        await update.message.reply_text(f"Logs for user ID {user_id_to_delete} have been deleted.")
    else:
        await update.message.reply_text("No logs found for this user ID.")

# Command to delete all logs
async def delete_all_logs(update: Update, context):
    for filename in os.listdir("assets/logs"):
        file_path = os.path.join("assets/logs", filename)
        os.remove(file_path)
    await update.message.reply_text("All logs have been deleted.")

# Command to view user IDs
async def view_ids(update: Update, context):
    ids = f"Your User ID: {update.effective_user.id}\n"
    ids += f"Sub-admin IDs: {sub_admins}\n"
    ids += f"All User IDs: {list(all_users)}"  # Convert set to list for display
    await update.message.reply_text(ids)
    
# Command to show the bot's rules
async def rules(update: Update, context):
    rules_text = (
        "Welcome to @anyencrypter_bot, Here are the rules to follow:\n"
        "1. Only send files in supported formats.\n"
        "2. Ensure files are under the specified size limit (20MB).\n"
        "3. Respect the privacy of other users and do not share their private information.\n"
        "4. Do not spam the bot with repeated requests.\n"
        "5. Follow all commands as instructed.\n"
        "6. For any issues, mail to: hey@xodivorce.in.\n"
    )
    await update.message.reply_text(rules_text)

    # Function to notify all users about a broadcast
async def notify_all_users(message: str):
    for user_id in all_users:  # Make sure `all_users` is defined elsewhere in your code
        try:
            await app.bot.send_message(user_id, message)
        except Exception as e:
            print(f"Failed to send message to User ID {user_id}: {e}")

# Function to notify all sub-admins and admin about the pending broadcast
async def notify_sub_admins(message: str):
    for user_id in sub_admins + [ADMIN_ID]:  # Notify all sub-admins and admin
        try:
            await app.bot.send_message(user_id, message)
        except Exception as e:
            print(f"Failed to send message to User ID {user_id}: {e}")

# Dictionary to keep track of pending broadcasts
pending_broadcasts = {}

# Function to handle the broadcast command
async def broadcast(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in sub_admins:
        await update.message.reply_text("You are not authorized to send a broadcast.")
        return

    if len(context.args) == 0:
        await update.message.reply_text("Usage: /broadcast <message>\nPlease provide a message to broadcast.")
        return

    # Join the message into a single string
    message = ' '.join(context.args)

    # Log the pending broadcast
    pending_broadcasts[user_id] = message

    # Function to handle the broadcast command
async def broadcast(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    if user_id == ADMIN_ID:
        # Admin can send broadcast directly
        if len(context.args) == 0:
            await update.message.reply_text("Usage: /broadcast <message>\nPlease provide a message to broadcast.")
            return
        
        # Join the message into a single string
        message = ' '.join(context.args)
        await notify_all_users(message)
        await update.message.reply_text(f"Admin broadcast sent: {message}")
        return

    if user_id not in sub_admins:
        await update.message.reply_text("You are not authorized to send a broadcast.")
        return

    if len(context.args) == 0:
        await update.message.reply_text("Usage: /broadcast <message>\nPlease provide a message to broadcast.")
        return

    # Join the message into a single string
    message = ' '.join(context.args)

    # Log the pending broadcast
    pending_broadcasts[user_id] = message

    # Notify admin and other sub-admins for approval
    approval_message = (
        f"Sub-admin ID {user_id} has requested a broadcast:\n\n"
        f"{message}\n\n"
        "Please approve or reject this broadcast by using\n /approve <sub_admin_id> or /reject <sub_admin_id>."
    )
    await notify_sub_admins(approval_message)

    await update.message.reply_text("Your broadcast request has been submitted for approval.")

# Function to approve the broadcast
async def approve_broadcast(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in sub_admins and user_id != ADMIN_ID:
        await update.message.reply_text("You are not authorized to approve broadcasts.")
        return

    if len(context.args) == 0:
        await update.message.reply_text("Usage: /approve <sub_admin_id>\nPlease provide the Sub-admin ID of the broadcast request.")
        return

    try:
        sub_admin_id = int(context.args[0])
        if sub_admin_id in pending_broadcasts:
            message = pending_broadcasts.pop(sub_admin_id)  # Remove the request from pending
            
            # Send the message to all users
            await notify_all_users(message)

            # Notify the sub-admin that their broadcast has been approved
            approval_notification = (
                f"Your broadcast request has been approved and sent to all users:\n\n"
                f"{message}"
            )
            await app.bot.send_message(chat_id=sub_admin_id, text=approval_notification)

            await update.message.reply_text(f"Broadcast approved and sent: {message}")
        else:
            await update.message.reply_text("No pending broadcast request found for this Sub-admin ID.")
    except ValueError:
        await update.message.reply_text("Invalid Sub-admin ID format. Please provide a valid user ID.")


# Function to reject the broadcast
async def reject_broadcast(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in sub_admins and user_id != ADMIN_ID:
        await update.message.reply_text("You are not authorized to reject broadcasts.")
        return

    if len(context.args) == 0:
        await update.message.reply_text("Usage: /reject <sub_admin_id>\nPlease provide the Sub-admin ID of the broadcast request.")
        return

    try:
        sub_admin_id = int(context.args[0])
        if sub_admin_id in pending_broadcasts:
            message = pending_broadcasts.pop(sub_admin_id)  # Remove the request from pending
            await update.message.reply_text(f"Broadcast request from Sub-admin ID {sub_admin_id} has been rejected.")
            # Notify the sub-admin about rejection
            await app.bot.send_message(chat_id=sub_admin_id, text="Your broadcast request has been rejected.")
        else:
            await update.message.reply_text("No pending broadcast request found for this Sub-admin ID.")
    except ValueError:
        await update.message.reply_text("Invalid Sub-admin ID format. Please provide a valid user ID.")

# Main function to start the bot
if __name__ == "__main__":
    load_sub_admins()
    app = ApplicationBuilder().token(TOKEN).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))  # Add help command
    app.add_handler(CommandHandler("rules", rules))  # Add rules command
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("approve", approve_broadcast))
    app.add_handler(CommandHandler("reject", reject_broadcast))
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
    app.add_handler(CommandHandler("delete_user_logs", delete_user_logs))
    app.add_handler(CommandHandler("delete_all_logs", delete_all_logs))
    app.add_handler(CommandHandler("view_id", view_ids))
    app.add_handler(MessageHandler(filters.Document.ALL, save_file))

    app.run_polling()
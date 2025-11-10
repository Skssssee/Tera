import logging
import json
import re 
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import httpx 

# --- Configuration ---
# Your Bot Token
BOT_TOKEN = "none"

# API for downloading content
API_BASE_URL = "https://teraapi.boogafantastic.workers.dev/api"

# Requested API IDs (Included for reference, but not used by this library)
API_ID = 27479878
API_HASH = "05f8dc8265d4c5df6376dded1d71c0ff"

# --- 1. Setup Logging ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- 2. Command Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a greeting message."""
    user_name = update.effective_user.first_name
    await update.message.reply_text(
        f"Hello {user_name}! I am a Terabox Downloader Bot.\n"
        f"Just **paste your Terabox link** directly in the chat to start the process."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a help message."""
    help_message = (
        "**Usage:**\n"
        "Simply **paste your Terabox shared link** (e.g., `https://terabox.app/s/...`) in the chat.\n\n"
        "I will fetch the details and give you a button to download/stream instantly in your browser."
    )
    await update.message.reply_text(help_message, parse_mode='Markdown')


async def auto_link_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Automatically detects links and processes them."""
    
    # We only process messages that have text
    if not update.message or not update.message.text:
        return
        
    text = update.message.text.strip()
    
    # Regex to find a pattern that suggests a Terabox link
    terabox_link_pattern = r"(https?://)?(terabox\.app|1024terabox\.com|www\.\w+\.com|t\.me/s/\w+)/s/[a-zA-Z0-9]+"

    match = re.search(terabox_link_pattern, text, re.IGNORECASE)
    
    if match:
        terabox_link = match.group(0)
        # Process the link
        await process_terabox_link(update, context, terabox_link)
    
    # If no link is found, the bot remains silent.


async def process_terabox_link(update: Update, context: ContextTypes.DEFAULT_TYPE, terabox_link: str):
    """
    Core function to process the link, fetch API data, and send the URL button 
    for browser redirection.
    """
    
    user_input = terabox_link.strip()
    full_api_url = f"{API_BASE_URL}?url={user_input}"
    
    await update.message.reply_text(f"🔍 Processing link: `{user_input}`\nThis may take a moment...", parse_mode='Markdown')
    
    try:
        # 2. Make the asynchronous request using httpx
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            response = await client.get(full_api_url, headers=headers)
        
        response.raise_for_status() 
        data = response.json()
        
        # --- Extracting from the 'files' list ---
        if data.get('status') != 'success' or not data.get('files'):
            error_message = data.get('message') or data.get('status') or "API returned no files."
            await update.message.reply_text(f"❌ API Failed: {error_message}")
            return

        file_info = data['files'][0]
        
        # Use stream_url (the proxy link) for the button URL
        download_url = file_info.get('stream_url') or file_info.get('direct_download_url')
        file_name = file_info.get('file_name', 'Unknown File') 
        thumbnail_url = file_info.get('thumbnails', {}).get('url2') 

        if download_url:
            # 4. Construct the Inline Keyboard (URL Button for Browser Redirect)
            button = InlineKeyboardButton("⬇️ Download / Stream in Browser", url=download_url)
            keyboard = InlineKeyboardMarkup([[button]])
            
            file_size = file_info.get('size', 'N/A')
            caption_text = f"✅ **File Found:** `{file_name}`\n\n**Size:** {file_size}\n\n_Click the button to open the download in your browser._"
            
            # Send the file details with the button
            if thumbnail_url:
                 try:
                    await update.message.reply_photo(
                        photo=thumbnail_url,
                        caption=caption_text,
                        reply_markup=keyboard, 
                        parse_mode='Markdown'
                    )
                 except Exception:
                     await update.message.reply_text(caption_text, reply_markup=keyboard, parse_mode='Markdown')
            else:
                 await update.message.reply_text(caption_text, reply_markup=keyboard, parse_mode='Markdown')
            
        else:
            await update.message.reply_text("❌ Could not find a valid stream or download link in the API response.")

    except httpx.HTTPStatusError as e:
        await update.message.reply_text(f"❌ API Status Error: The service returned status code **{e.response.status_code}**. Link might be blocked or invalid.")
        logging.error(f"HTTP Status Error: {e.response.status_code} for URL: {full_api_url}")
    except httpx.RequestError as e:
        await update.message.reply_text(f"❌ Network Error: Could not connect to the API (Timeout/Connection issue).")
        logging.error(f"Network Request Error: {e} for URL: {full_api_url}")
    except json.JSONDecodeError as e:
        await update.message.reply_text(f"❌ Parsing Error: The API response was not valid JSON.")
        logging.error(f"JSON Decode Error: {e}")
    except Exception as e:
        await update.message.reply_text(f"❌ An unexpected internal error occurred: {type(e).__name__}.")
        logging.error(f"Unexpected Python Error: {e}", exc_info=True)


# --- 4. Main Function ---

def main():
    """Starts the bot."""
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Register all handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command)) 

    # MESSAGE HANDLER (This listens for all non-command text messages and runs the auto-link handler)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_link_handler))

    print("🟢 Bot is running... Press Ctrl+C to stop.")
    application.run_polling()

if __name__ == '__main__':
    main()

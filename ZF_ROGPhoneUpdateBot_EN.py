import requests
from bs4 import BeautifulSoup
import telegram
import asyncio
import json
import os
import configparser
from telegram.helpers import escape_markdown
from datetime import datetime

# Read the settings from the config.ini file
config = configparser.ConfigParser()
config.read('config_EN.ini', encoding='utf-8')

TELEGRAM_BOT_TOKEN = config.get('Telegram', 'BOT_TOKEN')
TELEGRAM_CHANNEL_ID = config.get('Telegram', 'CHANNEL_ID')

# ASUS Release Notes URL
ASUS_UPDATE_URL = 'https://zentalk.asus.com/t5/release-notes/bg-p/rn_en'

# Sent announcements JSON file path
SENT_ANNOUNCEMENTS_FILE = 'sent_announcements_EN.json'

# Initialize the sent_announcements set
if os.path.exists(SENT_ANNOUNCEMENTS_FILE):
    with open(SENT_ANNOUNCEMENTS_FILE, 'r', encoding='utf-8') as file:
        sent_announcements = set(json.load(file))
else:
    sent_announcements = set()

# Define the date parsing function
def extract_date(announcement):
    # Assume the date format is [YYMMDD]
    date_str = announcement.split(']')[0][1:]
    return datetime.strptime(date_str, '%y%m%d')

# Get the latest announcements
def get_latest_announcements():
    response = requests.get(ASUS_UPDATE_URL)
    response.encoding = 'utf-8'  # Set the correct encoding
    soup = BeautifulSoup(response.text, 'html.parser')
    
    announcements = []
    for article in soup.find_all('article', class_='custom-blog-article-tile'):
        title = article.find('h3').text.strip()
        link = article.find('a')['href']
        full_link = f"https://zentalk.asus.com{link}"
        content = article.find('p').text.strip()
        
        announcements.append({
            'title': title,
            'link': full_link,
            'content': content
        })
    return announcements

# Send the announcement to the Telegram channel
async def send_to_telegram(announcement):
    bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
    # Use escape_markdown to escape the content
    title = escape_markdown(announcement['title'], version=2)
    content = escape_markdown(announcement['content'], version=2)
    link = escape_markdown(announcement['link'], version=2)
    message = (
        f"🚀 [{title}]\n\n"
        f"{content}\n\n"
        f"[View the full announcement]({link})"
    )
    await bot.send_message(
        chat_id=TELEGRAM_CHANNEL_ID,
        text=message,
        parse_mode='MarkdownV2',
        disable_web_page_preview=True
    )

# Main function: Check for new announcements and send to Telegram
async def main():
    global sent_announcements
    while True:
        try:
            announcements = get_latest_announcements()
            # Sort the announcements by date, from old to new
            sorted_announcements = sorted(announcements, key=lambda x: extract_date(x['title']))
            for announcement in sorted_announcements:
                if announcement['title'] not in sent_announcements:
                    await send_to_telegram(announcement)
                    sent_announcements.add(announcement['title'])
                    # Update the sent_announcements file
                    with open(SENT_ANNOUNCEMENTS_FILE, 'w', encoding='utf-8') as file:
                        json.dump(list(sent_announcements), file, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error: {e}")
        
        await asyncio.sleep(15)  # Every 15 seconds check once

if __name__ == '__main__':
    asyncio.run(main())

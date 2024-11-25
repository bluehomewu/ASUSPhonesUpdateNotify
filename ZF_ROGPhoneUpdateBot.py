import requests
from bs4 import BeautifulSoup
import telegram
import asyncio
import json
import os
import configparser
from telegram.helpers import escape_markdown
from datetime import datetime

# 讀取 config.ini 檔案中的設定
config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')

TELEGRAM_BOT_TOKEN = config.get('Telegram', 'BOT_TOKEN')
TELEGRAM_CHANNEL_ID = config.get('Telegram', 'CHANNEL_ID')

# ASUS 更新公告的網址
ASUS_UPDATE_URL = 'https://zentalk.asus.com/t5/更新公告/bg-p/RN_ZH'

# 已發送公告的 JSON 檔案路徑
SENT_ANNOUNCEMENTS_FILE = 'sent_announcements.json'

# 初始化已發送公告的集合
if os.path.exists(SENT_ANNOUNCEMENTS_FILE):
    with open(SENT_ANNOUNCEMENTS_FILE, 'r', encoding='utf-8') as file:
        sent_announcements = set(json.load(file))
else:
    sent_announcements = set()

# 定義日期解析函數
def extract_date(announcement):
    # 假設日期格式為 [YYMMDD]
    date_str = announcement.split(']')[0][1:]
    return datetime.strptime(date_str, '%y%m%d')

# 獲取最新公告的函數
def get_latest_announcements():
    response = requests.get(ASUS_UPDATE_URL)
    response.encoding = 'utf-8'  # 設定正確的編碼
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

# 發送公告到 Telegram 頻道的函數
async def send_to_telegram(announcement):
    bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
    # 使用 escape_markdown 轉義內容
    title = escape_markdown(announcement['title'], version=2)
    content = escape_markdown(announcement['content'], version=2)
    link = escape_markdown(announcement['link'], version=2)
    message = (
        f"🚀 [{title}]\n\n"
        f"{content}\n\n"
        f"[查看完整公告]({link})"
    )
    await bot.send_message(
        chat_id=TELEGRAM_CHANNEL_ID,
        text=message,
        parse_mode='MarkdownV2',
        disable_web_page_preview=True
    )

# 主函數：檢查新公告並發送到 Telegram
async def main():
    global sent_announcements
    while True:
        try:
            announcements = get_latest_announcements()
            # 將公告按日期排序，從遠到近
            sorted_announcements = sorted(announcements, key=lambda x: extract_date(x['title']))
            for announcement in sorted_announcements:
                if announcement['title'] not in sent_announcements:
                    await send_to_telegram(announcement)
                    sent_announcements.add(announcement['title'])
                    # 更新已發送公告的 JSON 檔案
                    with open(SENT_ANNOUNCEMENTS_FILE, 'w', encoding='utf-8') as file:
                        json.dump(list(sent_announcements), file, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error: {e}")
        
        await asyncio.sleep(15)  # 每 15 秒檢查一次

if __name__ == '__main__':
    asyncio.run(main())

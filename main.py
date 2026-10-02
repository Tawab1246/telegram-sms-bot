import requests
from bs4 import BeautifulSoup
import re
import time

TOKEN = "8350693240:AAEcPzL8QcRHAZzQ0eBigtZers3Z2zrPNk"
API_URL = f"https://api.telegram.org/bot{TOKEN}/"

SOURCES = [
    "https://7sim.org"
]

def send_msg(chat_id, text):
    try:
        requests.post(API_URL + "sendMessage", json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}, timeout=10)
    except Exception as e:
        print("Error sending msg:", e)

def get_numbers():
    numbers = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    for src in SOURCES:
        try:
            res = requests.get(src, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            for a in soup.find_all('a', href=True):
                href = a['href']
                text_content = a.get_text(strip=True)
                match = re.search(r'\+?\d{9,15}', text_content) or re.search(r'\+?\d{9,15}', href)
                if match:
                    num = match.group(0)
                    full_link = href if href.startswith('http') else src + (href if href.startswith('/') else '/' + href)
                    if not any(n['number'] == num for n in numbers):
                        numbers.append({'number': num, 'url': full_link})
        except Exception as e:
            print(f"Error fetching from {src}:", e)
    return numbers

def get_sms(number_url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    messages = []
    try:
        res = requests.get(number_url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        rows = soup.find_all(['tr', 'div'])
        for row in rows:
            text = row.get_text(separator=' | ', strip=True)
            if any(kw in text.lower() for kw in ['ago', 'min', 'sec', 'hour', 'day', 'code', 'verification', 'sms']):
                if len(text) > 15 and text not in messages:
                    messages.append(text[:200])
                    if len(messages) >= 5:
                        break
    except Exception as e:
        print("Error reading SMS:", e)
    return messages

def handle_updates():
    offset = 0
    print("ربات ابری فعال شد...")
    while True:
        try:
            res = requests.get(API_URL + f"getUpdates?offset={offset}&timeout=20", timeout=25).json()
            if "result" in res:
                for update in res["result"]:
                    offset = update["update_id"] + 1
                    if "message" in update and "text" in update["message"]:
                        chat_id = update["message"]["chat"]["id"]
                        text = update["message"]["text"].strip()
                        
                        if text in ["/start", "/help"]:
                            welcome = (
                                "🤖 <b>به ربات شماره مجازی عمومی خوش آمدید!</b>\n\n"
                                "دستورات موجود:\n"
                                "📱 /numbers - دریافت لیست شماره‌های فعال\n"
                                "📩 <code>/sms شماره</code> - دریافت پیامک‌های یک شماره\n"
                                "➕ <code>/add لینک</code> - افزودن منبع سایت جدید\n"
                                "ℹ️ /help - راهنمای ربات"
                            )
                            send_msg(chat_id, welcome)
                            
                        elif text == "/numbers":
                            send_msg(chat_id, "⏳ در حال استخراج شماره‌های جدید از منبع...")
                            nums = get_numbers()
                            if nums:
                                msg = "📱 <b>لیست شماره‌های مجازی فعال:</b>\n\n"
                                for idx, n in enumerate(nums[:15], 1):
                                    msg += f"{idx}. <code>{n['number']}</code>\n"
                                msg += "\nبرای دریافت پیامک، دستور زیر را بفرستید:\n"
                                msg += "<code>/sms شماره</code>"
                                send_msg(chat_id, msg)
                            else:
                                send_msg(chat_id, "❌ در حال حاضر شماره‌ای یافت نشد.")
                                
                        elif text.startswith("/sms"):
                            parts = text.split()
                            if len(parts) > 1:
                                target_num = parts[1].replace("+", "").strip()
                                send_msg(chat_id, f"🔍 در حال دریافت پیامک‌های شماره <code>{target_num}</code>...")
                                nums = get_numbers()
                                target_obj = next((n for n in nums if target_num in n['number']), None)
                                
                                if target_obj:
                                    sms_list = get_sms(target_obj['url'])
                                    if sms_list:
                                        msg = f"📩 <b>پیامک‌های دریافتی برای {target_num}:</b>\n\n"
                                        for sms in sms_list:
                                            msg += f"🔹 {sms}\n------------------\n"
                                        send_msg(chat_id, msg)
                                    else:
                                        send_msg(chat_id, "📭 هیچ پیامک جدیدی برای این شماره یافت نشد.")
                                else:
                                    send_msg(chat_id, "❌ شماره مورد نظر در لیست یافت نشد.")
                            else:
                                send_msg(chat_id, "⚠ لطفا شماره را وارد کنید.\nمثال: <code>/sms 447460692268</code>")
                                
                        elif text.startswith("/add"):
                            parts = text.split()
                            if len(parts) > 1:
                                new_url = parts[1].strip()
                                if new_url.startswith("http"):
                                    SOURCES.append(new_url)
                                    send_msg(chat_id, f"✅ منبع جدید با موفقیت اضافه شد:\n{new_url}")
                                else:
                                    send_msg(chat_id, "⚠️ لینک وارد شده معتبر نیست.")
                            else:
                                send_msg(chat_id, "⚠️ لطفاً آدرس سایت را وارد کنید.\nمثال: <code>/add https://site.com</code>")

        except Exception as e:
            time.sleep(3)

if __name__ == "__main__":
    handle_updates()


import telebot
import yt_dlp
import os
import random
from telebot import types
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "<b>Bot is running... 🚀</b>"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

BOT_TOKEN = os.environ.get('TOKEN')
ADMIN_ID = os.environ.get('ADMIN_ID')

MAINTENANCE_STATUS = {
    'youtube': True,
    'facebook': False,
    'instagram': False,
    'tiktok': False
}

if not BOT_TOKEN:
    print("Error: TOKEN is missing.")

bot = telebot.TeleBot(BOT_TOKEN)
users_file = "users.txt"
channel_file = "force_sub.txt"

BLOCKED_KEYWORDS = [
    "xnxx", "pornhub", "xvideos", "sex", "xxx", "nude", "pussy", 
    "dick", "cock", "boobs", "hentai", "milf", "sharmota", "neek", 
    "nik", "sks", "film sex", "سكس", "نيك", "اباحي"
]

SUCCESS_MSGS = [
    "🚀 عاش! جاري التجهيز...",
    "🎉 تم قفش الرابط!",
    "🫡 ثواني ويكون عندك...",
    "🔥 جاري المعالجة...",
    "📦 طلبك وصل!"
]

def is_safe_content(text):
    text = text.lower()
    for word in BLOCKED_KEYWORDS:
        if word in text:
            return False
    return True

def save_user(user_id):
    if not os.path.exists(users_file):
        with open(users_file, "w") as f: pass
    with open(users_file, "r") as f:
        users = f.read().splitlines()
    if str(user_id) not in users:
        with open(users_file, "a") as f:
            f.write(str(user_id) + "\n")
        return True
    return False

def check_sub(user_id):
    if not os.path.exists(channel_file): return True
    with open(channel_file, "r") as f: ch_user = f.read().strip()
    if not ch_user: return True
    try:
        member = bot.get_chat_member(ch_user, user_id)
        if member.status in ['creator', 'administrator', 'member']: return True
    except: return True
    return False

@bot.message_handler(commands=['start'])
def send_welcome(message):
    save_user(message.from_user.id)
    welcome_text = (
        f"أهلاً بك يا {message.from_user.first_name}! 👋\n\n"
        "🤖 أنا بوت التحميل الشامل\n"
        "أقدر أساعدك تحمل فيديوهات من أغلب\n"
        "المنصات بجودة عالية:\n\n"
        "1 يوتيوب (Youtube) ⚠️ (صيانة)\n"
        "2 تيك توك (TikTok) - بدون علامة مائية ✅\n"
        "3 إنستجرام (Reels & Posts) ✅\n"
        "4 فيسبوك (Facebook) ✅\n\n"
        "💡 طريقة الاستخدام:\n"
        "1 أرسل الرابط للتحميل المباشر\n"
        "2 أرسل اسم الفيديو للبحث عنه\n\n"
        "〰〰〰〰〰〰〰〰〰\n"
        "👨‍💻 المطور: @kareemcv"
    )

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("📢 قناة المطور", url="https://t.me/+8o0uI_JLmYwwZWJk"))
    
    current_user = str(message.from_user.id).strip()
    admin_clean = str(ADMIN_ID).strip() if ADMIN_ID else ""
    if admin_clean and current_user == admin_clean:
        markup.add(types.InlineKeyboardButton("👮‍♂️ لوحة التحكم", callback_data="admin_main"))

    try:
        with open('start_image.jpg', 'rb') as photo:
            bot.send_photo(message.chat.id, photo, caption=welcome_text, reply_markup=markup)
    except:
        bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_text = message.text
    user_id = message.from_user.id

    if not is_safe_content(user_text):
        bot.reply_to(message, "🚫 محتوى محظور!")
        return

    if not check_sub(user_id):
        bot.reply_to(message, "⚠️ يجب الاشتراك في القناة أولاً.")
        return

    if "http" in user_text:
        if ("youtube.com" in user_text or "youtu.be" in user_text) and MAINTENANCE_STATUS['youtube']:
            bot.reply_to(message, "⚠️ يوتيوب في الصيانة حالياً.\nجرب فيسبوك أو تيك توك.")
            return

        status_msg = bot.reply_to(message, "🔎 جاري الفحص...")
        
        try:
            ydl_opts = {'quiet': True, 'no_warnings': True, 'ignoreerrors': True, 'nocheckcertificate': True}
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(user_text, download=False)
            
            if not info:
                bot.edit_message_text("❌ الرابط لا يعمل.", chat_id=status_msg.chat.id, message_id=status_msg.message_id)
                return

            title = info.get('title', 'رابط الفيديو')
            linked_title = f"[{title}]({user_text})"

            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton("🎥 فيديو", callback_data=f"dl|video"),
                types.InlineKeyboardButton("🎵 صوت", callback_data=f"dl|audio")
            )
            markup.add(types.InlineKeyboardButton("❌ إلغاء", callback_data="cancel"))

            bot.delete_message(message.chat.id, status_msg.message_id)
            bot.reply_to(message, f"🎬 {linked_title}\n\n{random.choice(SUCCESS_MSGS)}\n👇 اختر الجودة:", parse_mode="Markdown", reply_markup=markup)

        except Exception as e:
            bot.edit_message_text(f"❌ خطأ: {str(e)}", chat_id=status_msg.chat.id, message_id=status_msg.message_id)

    else:
        markup = types.InlineKeyboardMarkup(row_width=2)
        yt_text = "🔴 يوتيوب (صيانة)" if MAINTENANCE_STATUS['youtube'] else "✅ يوتيوب"
        markup.add(types.InlineKeyboardButton(yt_text, callback_data="search_yt"))
        markup.add(types.InlineKeyboardButton("🔵 فيسبوك", callback_data="search_fb"))
        
        bot.reply_to(message, f"🧐 أين تريد البحث عن: {user_text} ؟", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    data = call.data
    
    if data == "cancel":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        return

    if data.startswith("dl|"):
        mode = data.split("|")[1]
        
        if not call.message.reply_to_message:
            bot.answer_callback_query(call.id, "❌ الرابط الأصلي مفقود.")
            return

        original_url = call.message.reply_to_message.text
        
        bot.edit_message_text(f"🚀 جاري التحميل...", chat_id=call.message.chat.id, message_id=call.message.message_id)
        
        try:
            ydl_opts = {
                'outtmpl': 'media/%(title)s.%(ext)s',
                'quiet': True,
                'max_filesize': 50*1024*1024,
                'nocheckcertificate': True
            }
            if mode == "audio": ydl_opts['format'] = 'bestaudio/best'
            else: ydl_opts['format'] = 'best[ext=mp4]/best'

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(original_url, download=True)
                filename = ydl.prepare_filename(info)
                caption = f"🤖 @kma_tbot"
                
                with open(filename, 'rb') as f:
                    if mode == "audio": bot.send_audio(call.message.chat.id, f, caption=caption)
                    else: bot.send_video(call.message.chat.id, f, caption=caption, supports_streaming=True)
                
                if os.path.exists(filename): os.remove(filename)
                bot.send_message(call.message.chat.id, "✅ تم!")

        except Exception as e:
            bot.send_message(call.message.chat.id, "❌ فشل التحميل.")

    elif data == "search_yt":
         bot.answer_callback_query(call.id, "⚠️ يوتيوب مغلق للصيانة!", show_alert=True)
         
    elif data == "search_fb":
         bot.answer_callback_query(call.id, "⚠️ ابحث في جوجل وابعتلي الرابط.", show_alert=True)

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()

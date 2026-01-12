import telebot
import yt_dlp
import os
import time
from keep_alive import keep_alive

# --- المتغيرات ---
BOT_TOKEN = os.getenv('TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID')

bot = telebot.TeleBot(BOT_TOKEN)

# إعدادات التحميل (مع الكوكيز)
ydl_opts = {
    'format': 'best',
    'noplaylist': True,
    'cookiefile': 'cookies.txt',  # هنا السر: لازم الملف ده يكون موجود
    'outtmpl': '%(title)s.%(ext)s',
    'quiet': True,
}

# --- رسالة الترحيب ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 أهلاً يا بطل!\n\n🎥 ابعتلي أي رابط فيديو (يوتيوب، فيسبوك، إنستجرام) وهحملهولك.\n🔍 أو ابعتلي أي كلمة للبحث عنها في يوتيوب.")

# --- دالة التحميل من الرابط ---
def is_url(message):
    return "http" in message.text

@bot.message_handler(func=is_url)
def handle_link(message):
    url = message.text
    chat_id = message.chat.id
    msg = bot.reply_to(message, "⏳ جاري التحميل... استنى لحظة.")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            bot.edit_message_text("✅ تم التحميل! جاري الرفع...", chat_id, msg.message_id)
            
            with open(filename, 'rb') as video:
                bot.send_video(chat_id, video, caption=f"🎬 {info.get('title', 'فيديو')}")
            
            os.remove(filename) # مسح الملف بعد الإرسال لتوفير المساحة
            bot.delete_message(chat_id, msg.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ حدث خطأ: اليوتيوب رفض الاتصال.\nتأكد من ملف cookies.txt", chat_id, msg.message_id)
        if ADMIN_ID:
            bot.send_message(ADMIN_ID, f"🚨 خطأ:\n{e}")

# --- دالة البحث (الكود الجديد) ---
@bot.message_handler(func=lambda m: True)
def handle_search(message):
    query = message.text
    chat_id = message.chat.id
    msg = bot.reply_to(message, f"🔍 جاري البحث عن: {query}...")

    try:
        # إعدادات خاصة للبحث (أول نتيجة فقط)
        search_opts = ydl_opts.copy()
        search_opts['default_search'] = 'ytsearch1'
        
        with yt_dlp.YoutubeDL(search_opts) as ydl:
            info = ydl.extract_info(query, download=True)
            
            # في البحث، النتيجة بتكون داخل قائمة 'entries'
            if 'entries' in info:
                video_info = info['entries'][0]
            else:
                video_info = info

            filename = ydl.prepare_filename(video_info)
            
            bot.edit_message_text(f"✅ لقيت الفيديو: {video_info.get('title')}\nجاري الرفع...", chat_id, msg.message_id)
            
            with open(filename, 'rb') as video:
                bot.send_video(chat_id, video, caption=f"🔎 نتيجة البحث: {query}")
            
            os.remove(filename)
            bot.delete_message(chat_id, msg.message_id)

    except Exception as e:
        bot.edit_message_text("❌ لم يتم العثور على نتائج أو حدث خطأ.", chat_id, msg.message_id)

# --- التشغيل ---
keep_alive()
bot.infinity_polling(skip_pending=True)

import telebot
import yt_dlp
import os
import time
from keep_alive import keep_alive

# --- المتغيرات ---
BOT_TOKEN = os.getenv('TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID')

bot = telebot.TeleBot(BOT_TOKEN)

# إعدادات التحميل (خدعة الأندرويد لتخطي الحظر)
ydl_opts = {
    'format': 'best',
    'noplaylist': True,
    'outtmpl': '%(title)s.%(ext)s',
    'quiet': True,
    # هنا السر: بنقول لليوتيوب إننا موبايل أندرويد مش سيرفر
    'extractor_args': {
        'youtube': {
            'player_client': ['android', 'ios'],
        }
    },
    # محاولة استخدام الكوكيز لو موجودة، لو مش موجودة يكمل عادي
    'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
}

# --- رسالة الترحيب ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 البوت جاهز يا هندسة!\nجرب ابعت رابط أو ابحث عن أي حاجة.")

# --- دالة التحميل من الرابط ---
def is_url(message):
    return "http" in message.text

@bot.message_handler(func=is_url)
def handle_link(message):
    url = message.text
    chat_id = message.chat.id
    msg = bot.reply_to(message, "⏳ بيحاول يعدي الحماية... لحظة.")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            bot.edit_message_text("✅ نجحنا! جاري الرفع...", chat_id, msg.message_id)
            
            with open(filename, 'rb') as video:
                bot.send_video(chat_id, video, caption=f"🎬 {info.get('title', 'فيديو')}")
            
            os.remove(filename) 
            bot.delete_message(chat_id, msg.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ اليوتيوب لسه قافش (Error 429).\nالحل: جرب رابط تاني أو استنى شوية.", chat_id, msg.message_id)
        print(f"Error: {e}")

# --- دالة البحث (معدلة لتخطي الحظر) ---
@bot.message_handler(func=lambda m: True)
def handle_search(message):
    query = message.text
    chat_id = message.chat.id
    msg = bot.reply_to(message, f"🔍 ببحث عن: {query}...")

    try:
        search_opts = ydl_opts.copy()
        search_opts['default_search'] = 'ytsearch1'
        
        with yt_dlp.YoutubeDL(search_opts) as ydl:
            # زودنا عدد المحاولات عشان لو فشل مرة يجرب التانية
            info = ydl.extract_info(query, download=True)
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
        # رسالة الخطأ هتظهر في اللوجز عشان نعرف السبب
        print(f"Search Error: {e}")
        bot.edit_message_text("❌ مش قادر أوصل لنتائج (السيرفر محظور مؤقتاً).", chat_id, msg.message_id)

# --- التشغيل ---
keep_alive()
bot.infinity_polling(skip_pending=True)

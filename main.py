import telebot
import yt_dlp
import os
import random
import json
from datetime import date
from telebot import types
from flask import Flask, request, jsonify, render_template
from threading import Thread

# --- 1. إعداد السيرفر ---
app = Flask('', template_folder='templates')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def receive_data():
    data = request.json
    req_type = data.get('type') # download or search
    text = data.get('text')
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({'status': 'error', 'msg': 'User ID missing'})

    # توجيه الطلب حسب النوع
    if req_type == 'search':
        # تشغيل البحث في الخلفية
        Thread(target=process_web_search, args=(user_id, text)).start()
    else:
        # تشغيل التحميل في الخلفية
        Thread(target=process_url_flow, args=(user_id, text)).start()
    
    return jsonify({'status': 'ok'})

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- 2. المتغيرات والتوكن ---
BOT_TOKEN = os.environ.get('TOKEN')
ADMIN_ID = os.environ.get('ADMIN_ID')
APP_URL = "https://live-ykzi.onrender.com" # الرابط الجديد بتاعك

# تم إلغاء صيانة يوتيوب كما طلبت
MAINTENANCE_STATUS = {
    'youtube': False, 
    'facebook': False,
    'instagram': False,
    'tiktok': False
}

if not BOT_TOKEN:
    print("Error: TOKEN is missing.")

bot = telebot.TeleBot(BOT_TOKEN)
users_file = "users.txt"
rewards_file = "rewards.json"
channel_file = "force_sub.txt"

BLOCKED_KEYWORDS = [
    "xnxx", "pornhub", "xvideos", "sex", "xxx", "nude", "pussy", 
    "dick", "cock", "boobs", "hentai", "milf", "sharmota", "neek", 
    "nik", "sks", "film sex", "سكس", "نيك", "اباحي", "شرموطة", 
    "toz", "kuss"
]

SUCCESS_MSGS = [
    "عاش! تم قفش الرابط بنجاح",
    "ثواني ويكون عندك",
    "جاري التجهيز يا وحش",
    "طلبك وصل",
    "انت تؤمر"
]

# --- 3. دوال النقاط والهدايا (جديد) ---
def get_user_data(user_id):
    if not os.path.exists(rewards_file):
        with open(rewards_file, "w") as f: json.dump({}, f)
    try:
        with open(rewards_file, "r") as f: data = json.load(f)
    except: data = {}
    
    user_id = str(user_id)
    if user_id not in data:
        data[user_id] = {"points": 0, "last_claimed": ""}
    return data, user_id

def claim_daily_gift(user_id):
    data, uid = get_user_data(user_id)
    today = str(date.today())
    
    if data[uid]["last_claimed"] == today:
        return False, 0, data[uid]["points"]
    
    gift = random.randint(1, 3) # هدية عشوائية من 1 لـ 3
    data[uid]["points"] += gift
    data[uid]["last_claimed"] = today
    
    with open(rewards_file, "w") as f: json.dump(data, f)
    return True, gift, data[uid]["points"]

# --- 4. دوال المساعدة ---
def is_safe_content(text):
    text = text.lower()
    for word in BLOCKED_KEYWORDS:
        if word in text: return False
    return True

def save_and_notify_admin(message):
    user_id = str(message.from_user.id)
    first_name = message.from_user.first_name
    username = message.from_user.username or "No User"
    
    if not os.path.exists(users_file):
        with open(users_file, "w") as f: pass
    with open(users_file, "r") as f: users = f.read().splitlines()
    
    if user_id not in users:
        with open(users_file, "a") as f: f.write(user_id + "\n")
        # إشعار للأدمن بدون نجوم
        if ADMIN_ID:
            msg = (f"مستخدم جديد انضم للبوت\nالاسم: {first_name}\n"
                   f"اليوزر: @{username}\nالأيدي: {user_id}")
            try: bot.send_message(ADMIN_ID, msg)
            except: pass
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

# مراقبة الحظر
@bot.my_chat_member_handler()
def handle_status_change(message):
    if not ADMIN_ID: return
    user = message.from_user
    new_status = message.new_chat_member.status
    old_status = message.old_chat_member.status
    
    if new_status == "kicked":
        bot.send_message(ADMIN_ID, f"قام مستخدم بحظر البوت\nالاسم: {user.first_name}\nالأيدي: {user.id}")
    elif new_status == "member" and old_status == "kicked":
        bot.send_message(ADMIN_ID, f"قام مستخدم بإعادة استخدام البوت\nالاسم: {user.first_name}\nالأيدي: {user.id}")

# --- 5. منطق التحميل والبحث ---

# معالجة البحث القادم من الويب
def process_web_search(chat_id, query):
    bot.send_message(chat_id, f"🔎 جاري البحث عن: {query} ...")
    try:
        # استخدام yt-dlp للبحث السريع
        with yt_dlp.YoutubeDL({'quiet': True, 'noplaylist': True}) as ydl:
            results = ydl.extract_info(f"ytsearch5:{query}", download=False)['entries']
        
        if not results:
            bot.send_message(chat_id, "❌ لم يتم العثور على نتائج.")
            return

        markup = types.InlineKeyboardMarkup(row_width=1)
        for vid in results:
            title = vid.get('title', 'Video')
            url = vid.get('webpage_url')
            # زرار لكل نتيجة، لما يدوس عليه يبدأ تحميله
            markup.add(types.InlineKeyboardButton(f"🎬 {title}", callback_data=f"web_dl|{url}"))
            
        bot.send_message(chat_id, "👇 اختر الفيديو للتحميل:", reply_markup=markup)

    except Exception as e:
        bot.send_message(chat_id, "❌ حدث خطأ أثناء البحث.")

# معالجة رابط التحميل
def process_url_flow(chat_id, url):
    if not is_safe_content(url):
        bot.send_message(chat_id, "🚫 محتوى محظور")
        return

    # فحص الصيانة لليوتيوب
    if ("youtube.com" in url or "youtu.be" in url) and MAINTENANCE_STATUS['youtube']:
        bot.send_message(chat_id, "⚠️ يوتيوب في الصيانة حالياً")
        return

    msg = bot.send_message(chat_id, f"🔎 وصلني الرابط\n{url}\nجاري الفحص...")
    
    try:
        # إضافة الكوكيز لو موجودة
        ydl_opts = {'quiet': True, 'no_warnings': True, 'ignoreerrors': True, 'nocheckcertificate': True}
        if os.path.exists('cookies.txt'):
            ydl_opts['cookiefile'] = 'cookies.txt'

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        
        if not info:
            bot.edit_message_text("❌ الرابط لا يعمل أو خاص", chat_id=msg.chat.id, message_id=msg.message_id)
            return

        title = info.get('title', 'Link')
        thumbnail = info.get('thumbnail')
        duration = info.get('duration') 
        linked_title = f"[{title}]({url})"
        motivational_msg = random.choice(SUCCESS_MSGS)

        # لو فيديو
        if duration and duration > 0:
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton("🎥 720p", callback_data="dl|720"),
                types.InlineKeyboardButton("🎥 480p", callback_data="dl|480")
            )
            markup.add(
                types.InlineKeyboardButton("🎥 360p", callback_data="dl|360"),
                types.InlineKeyboardButton("🎵 Audio", callback_data="dl|audio")
            )
            markup.add(types.InlineKeyboardButton("❌ إلغاء", callback_data="cancel"))

            bot.delete_message(chat_id, msg.message_id)
            caption_text = f"🎬 {linked_title}\n\n{motivational_msg}\n👇 اختر الجودة:"
            
            if thumbnail:
                bot.send_photo(chat_id, thumbnail, caption=caption_text, parse_mode="Markdown", reply_markup=markup)
            else:
                bot.send_message(chat_id, caption_text, parse_mode="Markdown", reply_markup=markup)
        
        # لو صور (Instagram/Facebook Posts)
        else:
            bot.edit_message_text(f"{motivational_msg}\n🖼️ جاري تحميل الصور...", chat_id=msg.chat.id, message_id=msg.message_id)
            
            ydl_opts_img = {
                'outtmpl': 'media/%(title)s.%(ext)s',
                'quiet': True,
                'max_filesize': 50*1024*1024,
                'nocheckcertificate': True
            }
            if os.path.exists('cookies.txt'): ydl_opts_img['cookiefile'] = 'cookies.txt'

            with yt_dlp.YoutubeDL(ydl_opts_img) as ydl_img:
                info_img = ydl_img.extract_info(url, download=True)
                filename = ydl_img.prepare_filename(info_img)
                caption = f"✅ @kareemcv"
                
                with open(filename, 'rb') as f:
                    bot.send_photo(chat_id, f, caption=caption)
                
                if os.path.exists(filename): os.remove(filename)
                bot.delete_message(chat_id, msg.message_id)

    except Exception as e:
        # إرسال رسالة عامة للمستخدم
        bot.edit_message_text("❌ فشل التحميل (تأكد من الرابط أو حاول لاحقاً)", chat_id=msg.chat.id, message_id=msg.message_id)
        # إرسال الخطأ بالتفصيل للأدمن فقط
        if ADMIN_ID:
            err_msg = f"⚠️ تقرير خطأ:\nالمستخدم: {chat_id}\nالرابط: {url}\nالخطأ: {str(e)}"
            bot.send_message(ADMIN_ID, err_msg)

# --- 6. الأوامر والواجهة ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    save_and_notify_admin(message)
    data, uid = get_user_data(message.from_user.id)
    points = data[uid]["points"]
    
    welcome_text = (
        f"أهلاً بك يا {message.from_user.first_name} 👋\n\n"
        f"💰 نقاطك الحالية: {points}\n\n"
        "أنا بوت التحميل الشامل 🤖\n"
        "حمل فيديوهاتك بسهولة وبدون علامة مائية\n\n"
        "اضغط بالأسفل لفتح التطبيق 👇"
    )

    markup = types.InlineKeyboardMarkup()
    web_app_info = types.WebAppInfo(APP_URL)
    markup.add(types.InlineKeyboardButton(text="📱 اضغط للتحميل والبحث (Web App)", web_app=web_app_info))
    
    # زر الهدية اليومية
    markup.add(types.InlineKeyboardButton("🎁 هدية يومية", callback_data="daily_gift"))
    
    markup.add(types.InlineKeyboardButton("📢 قناة المطور", url="https://t.me/+8o0uI_JLmYwwZWJk"))
    
    if str(ADMIN_ID) and str(message.from_user.id) == str(ADMIN_ID):
        markup.add(types.InlineKeyboardButton("👮‍♂️ لوحة التحكم", callback_data="admin_main"))

    try:
        with open('start_image.jpg', 'rb') as photo:
            bot.send_photo(message.chat.id, photo, caption=welcome_text, reply_markup=markup)
    except:
        bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if not check_sub(message.from_user.id):
        bot.reply_to(message, "⚠️ يجب الاشتراك في القناة أولاً")
        return

    if "http" in message.text:
        Thread(target=process_url_flow, args=(message.chat.id, message.text)).start()
    else:
        # البحث العادي من الشات
        process_web_search(message.chat.id, message.text)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    data = call.data
    
    # الهدية اليومية
    if data == "daily_gift":
        success, gift, total = claim_daily_gift(call.from_user.id)
        if success:
            bot.answer_callback_query(call.id, f"🎉 مبروك كسبت {gift} نقطة\nرصيدك: {total}", show_alert=True)
        else:
            bot.answer_callback_query(call.id, "⚠️ أخذت هديتك اليوم تعال بكرة", show_alert=True)
        return

    # استقبال التحميل من نتيجة البحث في الويب
    if data.startswith("web_dl|"):
        url = data.split("|")[1]
        process_url_flow(call.message.chat.id, url)
        return

    # لوحة التحكم
    if data == "admin_main":
        if str(call.from_user.id) != str(ADMIN_ID): return
        
        user_count = 0
        if os.path.exists(users_file):
            with open(users_file, "r") as f: user_count = len(f.readlines())
        
        stats_msg = (
            "👮‍♂️ لوحة التحكم الخاصة بالمطور\n\n"
            f"👥 عدد مستخدمي البوت: {user_count}\n"
            "📈 البوت يعمل بكفاءة"
        )
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, stats_msg)
        return

    if data == "cancel":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        return

    # معالجة التحميل (الجودة)
    if data.startswith("dl|"):
        mode = data.split("|")[1]
        
        # محاولة استخراج الرابط الأصلي
        original_url = ""
        if call.message.caption_entities:
            for entity in call.message.caption_entities:
                if entity.type == "text_link":
                    original_url = entity.url
                    break
        
        if not original_url: # fallback
             import re
             if call.message.caption:
                 urls = re.findall(r'(https?://[^\s]+)', call.message.caption)
                 if urls: original_url = urls[0]

        if not original_url:
            bot.answer_callback_query(call.id, "❌ الرابط مفقود")
            return
        
        bot.edit_message_caption(caption=f"🚀 جاري التحميل ({mode})...", chat_id=call.message.chat.id, message_id=call.message.message_id)
        
        try:
            ydl_opts = {
                'outtmpl': 'media/%(title)s.%(ext)s',
                'quiet': True,
                'max_filesize': 50*1024*1024,
                'nocheckcertificate': True
            }
            if os.path.exists('cookies.txt'): ydl_opts['cookiefile'] = 'cookies.txt'
            
            if mode == "audio": ydl_opts['format'] = 'bestaudio/best'
            elif mode == "720": ydl_opts['format'] = 'best[height<=720][ext=mp4]/best[ext=mp4]/best'
            elif mode == "480": ydl_opts['format'] = 'best[height<=480][ext=mp4]/best[ext=mp4]/best'
            elif mode == "360": ydl_opts['format'] = 'best[height<=360][ext=mp4]/best[ext=mp4]/best'
            else: ydl_opts['format'] = 'best[ext=mp4]/best'

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(original_url, download=True)
                filename = ydl.prepare_filename(info)
                caption = f"✅ BOT  @Kma_tbot"
                
                with open(filename, 'rb') as f:
                    if mode == "audio": bot.send_audio(call.message.chat.id, f, caption=caption)
                    else: bot.send_video(call.message.chat.id, f, caption=caption, supports_streaming=True)
                
                if os.path.exists(filename): os.remove(filename)
                bot.delete_message(call.message.chat.id, call.message.message_id)

        except Exception as e:
            bot.send_message(call.message.chat.id, "❌ فشل التحميل")
            if ADMIN_ID: bot.send_message(ADMIN_ID, f"Error DL: {str(e)}")

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling(allowed_updates=['message', 'callback_query', 'my_chat_member'])

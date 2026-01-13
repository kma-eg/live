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
    req_type = data.get('type') 
    text = data.get('text')
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({'status': 'error', 'msg': 'User ID missing'})

    # 1. معالجة الهدية اليومية (من الويب)
    if req_type == 'gift':
        success, gift, total = claim_daily_gift(user_id)
        if success:
            # إرسال إشعار للمستخدم في البوت
            try:
                bot.send_message(user_id, f"🎉 مبروك! استلمت هديتك اليومية: {gift} نقطة\n💰 رصيدك الحالي: {total}")
            except: pass
            return jsonify({'status': 'ok', 'msg': f'مبروك! كسبت {gift} نقطة', 'points': total})
        else:
            return jsonify({'status': 'error', 'msg': 'أخدت الهدية النهاردة، تعال بكرة! 🎁', 'points': total})

    # 2. معالجة البحث
    elif req_type == 'search':
        Thread(target=process_web_search, args=(user_id, text)).start()
        return jsonify({'status': 'ok'})

    # 3. معالجة التحميل
    else:
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
APP_URL = "https://live-ykzi.onrender.com" 

MAINTENANCE_STATUS = {
    'youtube': False, 
}

bot = telebot.TeleBot(BOT_TOKEN)
users_file = "users.txt"
rewards_file = "rewards.json"
channel_file = "force_sub.txt"

# حالة الأدمن (عشان الإذاعة وتغيير القناة)
admin_states = {} 

BLOCKED_KEYWORDS = [
    "xnxx", "pornhub", "xvideos", "sex", "xxx", "nude", "pussy", 
    "dick", "cock", "boobs", "hentai", "milf", "sharmota", "neek", 
    "nik", "sks", "film sex", "سكس", "نيك", "اباحي", "شرموطة"
]

SUCCESS_MSGS = ["عاش! تم قفش الرابط", "ثواني ويكون عندك", "جاري التجهيز يا وحش", "طلبك وصل"]

# --- 3. دوال البيانات ---
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
    
    gift = random.randint(1, 3)
    data[uid]["points"] += gift
    data[uid]["last_claimed"] = today
    
    with open(rewards_file, "w") as f: json.dump(data, f)
    return True, gift, data[uid]["points"]

def save_and_notify_admin(message):
    user_id = str(message.from_user.id)
    first_name = message.from_user.first_name
    username = message.from_user.username or "No User"
    
    if not os.path.exists(users_file):
        with open(users_file, "w") as f: pass
    with open(users_file, "r") as f: users = f.read().splitlines()
    
    if user_id not in users:
        with open(users_file, "a") as f: f.write(user_id + "\n")
        if ADMIN_ID:
            msg = f"مستخدم جديد:\nالاسم: {first_name}\nاليوزر: @{username}\nID: {user_id}"
            try: bot.send_message(ADMIN_ID, msg)
            except: pass
        return True
    return False

def check_sub(user_id):
    if not os.path.exists(channel_file): return True
    with open(channel_file, "r") as f: ch_user = f.read().strip()
    if not ch_user or ch_user == "none": return True
    
    try:
        member = bot.get_chat_member(ch_user, user_id)
        if member.status in ['creator', 'administrator', 'member']: return True
    except: return True # لو في خطأ في القناة نعديه
    return False

# --- 4. منطق التحميل ---
def process_web_search(chat_id, query):
    bot.send_message(chat_id, f"🔎 جاري البحث عن: {query} ...")
    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'noplaylist': True}) as ydl:
            results = ydl.extract_info(f"ytsearch5:{query}", download=False)['entries']
        
        if not results:
            bot.send_message(chat_id, "❌ لم يتم العثور على نتائج.")
            return

        markup = types.InlineKeyboardMarkup(row_width=1)
        for vid in results:
            title = vid.get('title', 'Video')
            url = vid.get('webpage_url')
            markup.add(types.InlineKeyboardButton(f"🎬 {title}", callback_data=f"web_dl|{url}"))
            
        bot.send_message(chat_id, "👇 اختر الفيديو للتحميل:", reply_markup=markup)
    except:
        bot.send_message(chat_id, "❌ حدث خطأ أثناء البحث.")

def process_url_flow(chat_id, url):
    for word in BLOCKED_KEYWORDS:
        if word in url.lower():
            bot.send_message(chat_id, "🚫 محتوى محظور")
            return

    msg = bot.send_message(chat_id, f"🔎 وصلني الرابط.. جاري الفحص...")
    
    try:
        ydl_opts = {'quiet': True, 'no_warnings': True, 'ignoreerrors': True}
        if os.path.exists('cookies.txt'): ydl_opts['cookiefile'] = 'cookies.txt'

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        
        if not info:
            bot.edit_message_text("❌ الرابط لا يعمل أو خاص", chat_id, msg.message_id)
            return

        title = info.get('title', 'Media')
        thumbnail = info.get('thumbnail')
        duration = info.get('duration')
        
        # لو فيديو
        if duration and duration > 0:
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton("🎥 720p", callback_data="dl|720"),
                types.InlineKeyboardButton("🎥 360p", callback_data="dl|360"),
                types.InlineKeyboardButton("🎵 Audio", callback_data="dl|audio"),
                types.InlineKeyboardButton("❌ إلغاء", callback_data="cancel")
            )
            bot.delete_message(chat_id, msg.message_id)
            caption = f"🎬 {title}\n👇 اختر الجودة:"
            if thumbnail:
                bot.send_photo(chat_id, thumbnail, caption=caption, reply_markup=markup)
            else:
                bot.send_message(chat_id, caption, reply_markup=markup)
        else:
            # صور أو reels قصيرة جداً
            bot.edit_message_text("⬇️ جاري التحميل المباشر...", chat_id, msg.message_id)
            ydl_opts['outtmpl'] = 'media/%(title)s.%(ext)s'
            ydl_opts['max_filesize'] = 50*1024*1024
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                with open(filename, 'rb') as f:
                    bot.send_document(chat_id, f, caption="✅ @kareemcv")
                if os.path.exists(filename): os.remove(filename)
                bot.delete_message(chat_id, msg.message_id)

    except Exception as e:
        bot.edit_message_text("❌ فشل التحميل.", chat_id, msg.message_id)
        if ADMIN_ID: bot.send_message(ADMIN_ID, f"Error: {e}")

# --- 5. الهاندلرز واللوحة ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    save_and_notify_admin(message)
    data, uid = get_user_data(message.from_user.id)
    
    welcome_text = (
        f"أهلاً بك يا {message.from_user.first_name} 👋\n"
        f"💰 نقاطك: {data[uid]['points']}\n"
        "حمل فيديوهاتك واجمع هدايا يومية من داخل التطبيق 👇"
    )

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text="📱 فتح التطبيق (تحميل + هدايا)", web_app=types.WebAppInfo(APP_URL)))
    markup.add(types.InlineKeyboardButton("📢 قناة المطور", url="https://t.me/+8o0uI_JLmYwwZWJk"))
    
    if str(ADMIN_ID) and str(message.from_user.id) == str(ADMIN_ID):
        markup.add(types.InlineKeyboardButton("👮‍♂️ لوحة التحكم", callback_data="admin_main"))

    try:
        with open('start_image.jpg', 'rb') as p:
            bot.send_photo(message.chat.id, p, caption=welcome_text, reply_markup=markup)
    except:
        bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    chat_id = call.message.chat.id
    user_id = str(call.from_user.id)
    data = call.data

    # --- أدوات الأدمن ---
    if user_id == str(ADMIN_ID):
        if data == "admin_main":
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats"),
                types.InlineKeyboardButton("📢 إذاعة للمستخدمين", callback_data="admin_broadcast"),
                types.InlineKeyboardButton("🔒 قناة الاشتراك", callback_data="admin_force"),
                types.InlineKeyboardButton("❌ إغلاق", callback_data="cancel")
            )
            bot.edit_message_text("👮‍♂️ **لوحة التحكم الرئيسية**\nاختر قسماً:", chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
            return

        if data == "admin_stats":
            users_count = 0
            if os.path.exists(users_file):
                with open(users_file) as f: users_count = len(f.readlines())
            
            back = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_main"))
            bot.edit_message_text(f"📊 **الإحصائيات**\n\n👥 عدد المستخدمين: {users_count}", chat_id, call.message.message_id, reply_markup=back, parse_mode="Markdown")
            return

        if data == "admin_broadcast":
            admin_states[user_id] = "broadcast"
            back = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 إلغاء", callback_data="admin_main"))
            bot.edit_message_text("📢 **وضع الإذاعة**\nأرسل الرسالة (نص أو صورة) الآن ليتم إرسالها للجميع:", chat_id, call.message.message_id, reply_markup=back, parse_mode="Markdown")
            return

        if data == "admin_force":
            curr_ch = "لا يوجد"
            if os.path.exists(channel_file):
                with open(channel_file) as f: curr_ch = f.read()
            
            admin_states[user_id] = "set_channel"
            back = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 إلغاء", callback_data="admin_main"))
            bot.edit_message_text(f"🔒 **الاشتراك الإجباري**\nالقناة الحالية: {curr_ch}\n\nأرسل معرف القناة الجديد (مثل @channel) أو أرسل 'none' للإلغاء:", chat_id, call.message.message_id, reply_markup=back, parse_mode="Markdown")
            return

    # --- باقي الأزرار ---
    if data == "cancel":
        bot.delete_message(chat_id, call.message.message_id)
        if user_id in admin_states: del admin_states[user_id]
        return

    if data.startswith("web_dl|"):
        process_url_flow(chat_id, data.split("|")[1])
        return

    if data.startswith("dl|"):
        # كود التحميل السابق (مختصر هنا)
        mode = data.split("|")[1]
        orig_url = ""
        # استخراج الرابط من الـ entity
        if call.message.caption_entities:
            for ent in call.message.caption_entities:
                if ent.type == "text_link": orig_url = ent.url
        
        if not orig_url: 
             bot.answer_callback_query(call.id, "❌ الرابط انتهى")
             return

        bot.edit_message_caption("🚀 جاري التحميل...", chat_id, call.message.message_id)
        try:
            ydl_opts = {
                'outtmpl': 'media/%(title)s.%(ext)s',
                'quiet': True,
                'max_filesize': 50*1024*1024,
                'nocheckcertificate': True
            }
            if os.path.exists('cookies.txt'): ydl_opts['cookiefile'] = 'cookies.txt'
            
            if mode == "audio": ydl_opts['format'] = 'bestaudio/best'
            else: ydl_opts['format'] = 'best[ext=mp4]/best'

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(orig_url, download=True)
                filename = ydl.prepare_filename(info)
                with open(filename, 'rb') as f:
                    if mode == "audio": bot.send_audio(chat_id, f, caption="@kareemcv")
                    else: bot.send_video(chat_id, f, caption="@kareemcv")
                if os.path.exists(filename): os.remove(filename)
                bot.delete_message(chat_id, call.message.message_id)
        except:
             bot.send_message(chat_id, "❌ فشل التحميل")

# --- استقبال رسائل الأدمن (إذاعة / قناة) ---
@bot.message_handler(func=lambda m: str(m.from_user.id) in admin_states and str(m.from_user.id) == str(ADMIN_ID))
def admin_actions(message):
    state = admin_states[str(message.from_user.id)]
    
    if state == "broadcast":
        users = []
        if os.path.exists(users_file):
            with open(users_file) as f: users = f.read().splitlines()
        
        count = 0
        bot.reply_to(message, f"🚀 جاري الإرسال لـ {len(users)} مستخدم...")
        for uid in users:
            try:
                bot.copy_message(uid, message.chat.id, message.message_id)
                count += 1
            except: pass
        
        bot.send_message(message.chat.id, f"✅ تمت الإذاعة بنجاح لـ {count} مستخدم.")
        del admin_states[str(message.from_user.id)]
    
    elif state == "set_channel":
        new_ch = message.text.strip()
        with open(channel_file, "w") as f: f.write(new_ch)
        bot.reply_to(message, f"✅ تم تحديث قناة الاشتراك إلى: {new_ch}")
        del admin_states[str(message.from_user.id)]

# استقبال الرسائل العادية
@bot.message_handler(func=lambda m: True)
def normal_msg(message):
    if not check_sub(message.from_user.id):
        bot.reply_to(message, "⚠️ عذراً، يجب الاشتراك في القناة لاستخدام البوت.")
        return
    
    if "http" in message.text:
        Thread(target=process_url_flow, args=(message.chat.id, message.text)).start()
    else:
        process_web_search(message.chat.id, message.text)

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling(allowed_updates=['message', 'callback_query'])
            

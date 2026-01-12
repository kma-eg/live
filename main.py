import telebot
import yt_dlp
import os
from telebot import types
from flask import Flask
from threading import Thread
import time

# ------------------- 1. تشغيل السيرفر (Keep Alive) -------------------
app = Flask('')

@app.route('/')
def home():
    return "<b>Bot is running... 🚀</b>"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ------------------- 2. إعدادات البوت -------------------
BOT_TOKEN = os.environ.get('TOKEN')
ADMIN_ID = os.environ.get('ADMIN_ID')

if not BOT_TOKEN:
    print("Error: TOKEN is missing.")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)
users_file = "users.txt"
channel_file = "force_sub.txt" # ملف لحفظ قناة الاشتراك

# ------------------- 3. دوال التخزين والمساعدة -------------------
def save_user(user_id):
    # دالة ذكية: بترجع True لو المستخدم جديد، و False لو قديم
    if not os.path.exists(users_file):
        with open(users_file, "w") as f: pass
    with open(users_file, "r") as f:
        users = f.read().splitlines()
    
    if str(user_id) not in users:
        with open(users_file, "a") as f:
            f.write(str(user_id) + "\n")
        return True # مستخدم جديد
    return False # مستخدم قديم (عاد للبوت)

def get_users_count():
    if not os.path.exists(users_file): return 0
    with open(users_file, "r") as f:
        return len(f.read().splitlines())

def set_force_channel(channel_user):
    with open(channel_file, "w") as f:
        f.write(channel_user)

def get_force_channel():
    if not os.path.exists(channel_file): return None
    with open(channel_file, "r") as f:
        ch = f.read().strip()
    return ch if ch else None

def check_sub(user_id):
    ch_user = get_force_channel()
    if not ch_user: return True # لو مفيش قناة، البوت مفتوح
    try:
        member = bot.get_chat_member(ch_user, user_id)
        if member.status in ['creator', 'administrator', 'member']:
            return True
    except:
        return True # لو حصل خطأ (البوت مش أدمن) نعدي المستخدم عشان البوت ميقفش
    return False

# ------------------- 4. أمر Start (التصميم الأصلي + المميزات) -------------------
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    
    # -- 1. التحقق من الاشتراك الإجباري --
    if not check_sub(user_id):
        ch_user = get_force_channel()
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("اشترك في القناة أولاً 🔔", url=f"https://t.me/{ch_user.replace('@', '')}"))
        markup.add(types.InlineKeyboardButton("تم الاشتراك ✅", callback_data="check_sub_status"))
        bot.send_message(user_id, f"⚠️ عذراً عزيزي\nعليك الاشتراك في قناة البوت لتتمكن من استخدامه.\n\nالقناة: {ch_user}", reply_markup=markup)
        return

    # -- 2. نظام التنبيهات (جديد vs عائد) --
    is_new = save_user(user_id)
    if ADMIN_ID:
        try:
            # تجهيز رابط لاسم المستخدم
            name = message.from_user.first_name
            username = f"@{message.from_user.username}" if message.from_user.username else "لا يوجد"
            
            if is_new:
                # رسالة مستخدم جديد
                msg = f"➕ **مستخدم جديد:**\nالاسم: {name}\nاليوزر: {username}\nالأيدي: `{user_id}`"
                bot.send_message(ADMIN_ID, msg, parse_mode="Markdown")
            else:
                # رسالة العودة (اللي طلبتها)
                msg = f"📊 **قام مستخدم بإعادة استخدام البوت:**\nالاسم: {name}\nاليوزر: {username}\nالأيدي: `{user_id}`"
                bot.send_message(ADMIN_ID, msg, parse_mode="Markdown")
        except: pass

    # -- 3. رسالة الترحيب (التصميم الأصلي - صورة 1) --
    # لاحظ: شلت النجوم ** عشان الكلام يبقى عادي زي ما طلبت
    welcome_text = (
        f"أهلاً بك يا {message.from_user.first_name}! 👋\n\n"
        "🤖 أنا بوت التحميل الشامل\n"
        "أقدر أساعدك تحمل فيديوهات من أغلب\n"
        "المنصات بجودة عالية:\n\n"
        "1 يوتيوب (Youtube) ✅\n"
        "2 تيك توك (TikTok) - بدون علامة مائية ✅\n"
        "3 إنستجرام (Reels & Posts) ✅\n"
        "4 فيسبوك (Facebook) ✅\n\n"
        "💡 طريقة الاستخدام:\n"
        "1 أرسل الرابط للتحميل المباشر\n"
        "2 أرسل اسم الفيديو للبحث عنه في\n"
        "يوتيوب 🔍\n\n"
        "〰〰〰〰〰〰〰〰〰\n"
        "🤖 بوت: @kma_tbot\n"
        "👨‍💻 المطور: @kareemcv"
    )

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("📢 قناة المطور", url="https://t.me/+8o0uI_JLmYwwZWJk"))
    
    # زرار الأدمن (يظهر للمطور فقط)
    current_user = str(message.from_user.id).strip()
    admin_clean = str(ADMIN_ID).strip() if ADMIN_ID else ""
    if admin_clean and current_user == admin_clean:
        markup.add(types.InlineKeyboardButton("👮‍♂️ لوحة التحكم (Admin)", callback_data="admin_main"))

    try:
        with open('start_image.jpg', 'rb') as photo:
            bot.send_photo(message.chat.id, photo, caption=welcome_text, reply_markup=markup)
    except:
        bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

# ------------------- 5. معالجة الرسائل (الجوهر) -------------------
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    # تحقق من الاشتراك قبل الرد
    if not check_sub(message.from_user.id):
        bot.reply_to(message, "⚠️ يجب عليك الاشتراك في القناة أولاً، ثم اضغط /start")
        return

    text = message.text
    
    # --- حالة الرابط (تحميل) ---
    if "http" in text:
        status_msg = bot.reply_to(message, "🔎 جاري المعالجة...")
        try:
            ydl_opts = {
                'quiet': True, 'no_warnings': True, 'ignoreerrors': True, 'cookiefile': 'cookies.txt',
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(text, download=False)
            
            if not info:
                bot.edit_message_text("❌ الرابط لا يعمل.", chat_id=status_msg.chat.id, message_id=status_msg.message_id)
                return

            title = info.get('title', 'فيديو')
            thumbnail = info.get('thumbnail')
            
            # الأزرار (بسيطة ومباشرة)
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(types.InlineKeyboardButton("🎬 تحميل فيديو", callback_data="dl_video"))
            markup.add(types.InlineKeyboardButton("🎵 تحميل صوت", callback_data="dl_audio"))
            
            # إرسال الصورة + الأزرار (بدون نجوم في الكابشن)
            if thumbnail:
                bot.send_photo(message.chat.id, thumbnail, caption=f"🎬 {title}", reply_to_message_id=message.message_id, reply_markup=markup)
            else:
                bot.reply_to(message, f"🎬 {title}", reply_markup=markup)
            
            bot.delete_message(message.chat.id, status_msg.message_id)

        except Exception as e:
            bot.edit_message_text(f"❌ خطأ: {str(e)}", chat_id=status_msg.chat.id, message_id=status_msg.message_id)
        
    # --- حالة النص (بحث) ---
    else:
        msg = bot.reply_to(message, f"🔍 جاري البحث عن: {text}...")
        try:
            ydl_opts = {'quiet': True, 'default_search': 'ytsearch8', 'extract_flat': True, 'ignoreerrors': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(text, download=False)
            
            markup = types.InlineKeyboardMarkup(row_width=1)
            if 'entries' in info and info['entries']:
                for entry in info['entries']:
                    title = entry.get('title')
                    vid_id = entry.get('id')
                    if title and vid_id:
                        markup.add(types.InlineKeyboardButton(f"🎬 {title}", callback_data=f"sel|{vid_id}"))
                bot.edit_message_text(f"✅ نتائج البحث: {text}", chat_id=message.chat.id, message_id=msg.message_id, reply_markup=markup)
            else:
                bot.edit_message_text("❌ لا توجد نتائج.", chat_id=message.chat.id, message_id=msg.message_id)
        except:
            bot.edit_message_text("❌ خطأ في البحث.", chat_id=message.chat.id, message_id=msg.message_id)

# ------------------- 6. معالج الأزرار ولوحة التحكم -------------------
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    data = call.data
    
    # --- أوامر التحميل ---
    if data.startswith("sel|"): # اختيار من البحث
        vid_id = data.split("|")[1]
        link = f"https://youtu.be/{vid_id}"
        call.message.text = link
        handle_message(call.message) # نبعته لدالة المعالجة كأنه رابط
        bot.delete_message(call.message.chat.id, call.message.message_id)

    elif data in ["dl_video", "dl_audio"]: # تنفيذ التحميل
        try:
            if call.message.reply_to_message:
                original_link = call.message.reply_to_message.text
                start_download_final(call.message, original_link, data)
            else:
                bot.answer_callback_query(call.id, "❌ الرابط مفقود.")
        except: pass

    # --- التحقق من الاشتراك ---
    elif data == "check_sub_status":
        if check_sub(call.from_user.id):
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, "✅ شكراً لاشتراكك! الآن يمكنك استخدام البوت.\nأرسل /start")
        else:
            bot.answer_callback_query(call.id, "❌ لم تشترك بعد!", show_alert=True)

    # --- لوحة التحكم (الجديدة المبسطة) ---
    elif data == "admin_main":
        if str(call.from_user.id).strip() != str(ADMIN_ID).strip(): return
        
        # تصميم اللوحة زي ما طلبت (أزرار واضحة)
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("📢 الإذاعة", callback_data="admin_broadcast"),
                   types.InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats"))
        markup.add(types.InlineKeyboardButton("🔒 اشتراك إجباري", callback_data="admin_force_sub"))
        markup.add(types.InlineKeyboardButton("❌ إغلاق", callback_data="close_admin"))
        
        bot.edit_message_caption("👮‍♂️ **لوحة التحكم الرئيسية**", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

    elif data == "admin_stats":
        count = get_users_count()
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_main"))
        bot.edit_message_caption(f"📊 **إحصائيات البوت:**\n\n👥 عدد الأعضاء: {count}", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

    elif data == "admin_broadcast":
        msg = bot.send_message(call.message.chat.id, "📝 **أرسل الرسالة التي تريد إذاعتها الآن (نص، صورة، فيديو):**")
        bot.register_next_step_handler(msg, broadcast_logic)

    elif data == "admin_force_sub":
        current_ch = get_force_channel()
        msg_text = f"🔒 **قناة الاشتراك الإجباري الحالية:** {current_ch if current_ch else 'لا يوجد'}\n\nأرسل معرف القناة الجديد الآن (مثال: @channel)\nأو أرسل 'حذف' لإلغاء الاشتراك."
        msg = bot.send_message(call.message.chat.id, msg_text)
        bot.register_next_step_handler(msg, set_channel_logic)

    elif data == "close_admin":
        bot.delete_message(call.message.chat.id, call.message.message_id)

# ------------------- 7. المنطق (Logic) -------------------

# دالة الإذاعة
def broadcast_logic(message):
    if message.text == "إلغاء":
        bot.reply_to(message, "تم الإلغاء.")
        return
    
    if not os.path.exists(users_file): return
    with open(users_file, "r") as f: users = f.read().splitlines()
    
    success = 0
    failed = 0
    status_msg = bot.reply_to(message, "🚀 جاري الإذاعة... يرجى الانتظار")
    
    for uid in users:
        try:
            bot.copy_message(uid, message.chat.id, message.message_id)
            success += 1
        except:
            failed += 1
    
    bot.edit_message_text(f"✅ **تمت الإذاعة بنجاح!**\n\n✅ ناجح: {success}\n❌ فاشل: {failed}", chat_id=message.chat.id, message_id=status_msg.message_id)

# دالة تعيين القناة
def set_channel_logic(message):
    text = message.text
    if text == "حذف":
        set_force_channel("")
        bot.reply_to(message, "✅ تم إلغاء الاشتراك الإجباري.")
    elif text.startswith("@"):
        set_force_channel(text)
        bot.reply_to(message, f"✅ تم تعيين قناة الاشتراك: {text}\n\n⚠️ **تنبيه:** تأكد أن البوت (Admin) في القناة ليعمل التحقق!")
    else:
        bot.reply_to(message, "❌ خطأ! المعرف يجب أن يبدأ بـ @")

# دالة التحميل النهائية (الكوكيز + التوقيع الجديد)
def start_download_final(message, link, type_dl):
    bot.edit_message_caption(caption="⏳ جاري التحميل...", chat_id=message.chat.id, message_id=message.message_id)
    
    try:
        ydl_opts = {
            'outtmpl': 'media/%(title)s.%(ext)s',
            'quiet': True,
            'max_filesize': 50*1024*1024,
            'cookiefile': 'cookies.txt', # الكوكيز اللي هترفعها
            'nocheckcertificate': True
        }

        if type_dl == "dl_audio":
            ydl_opts['format'] = 'bestaudio/best'
        else:
            ydl_opts['format'] = 'best[ext=mp4]/best' # يضمن ملف MP4 سليم

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=True)
            filename = ydl.prepare_filename(info)
            
            # التوقيع الجديد (بوت فقط)
            caption = f"🤖 Bot: @kma_tbot"

            with open(filename, 'rb') as f:
                if type_dl == "dl_audio": 
                    bot.send_audio(message.chat.id, f, caption=caption)
                else: 
                    bot.send_video(message.chat.id, f, caption=caption, supports_streaming=True)
            
            if os.path.exists(filename): os.remove(filename)

    except Exception as e:
        bot.send_message(message.chat.id, "❌ فشل التحميل (تأكد من صلاحية الكوكيز أو حجم الملف).")

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()

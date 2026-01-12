import telebot
import yt_dlp
import os
import time
from keep_alive import keep_alive

# --- إعدادات البوت والمتغيرات ---
# بنجيب التوكن والآيدي من إعدادات السيرفر (Environment Variables)
BOT_TOKEN = os.getenv('TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID')

# التأكد من وجود التوكن
if not BOT_TOKEN:
    print("خطأ: لم يتم العثور على التوكن. تأكد من إضافته في متغيرات البيئة في Render.")
    exit()

bot = telebot.TeleBot(BOT_TOKEN)

# إعدادات التحميل (yt-dlp) - أساسية
ydl_opts_base = {
    'format': 'best',
    'noplaylist': True,
    # هنا ممكن نضيف مسار ملف الكوكيز لو رفعناه على GitHub
    # 'cookiefile': 'cookies.txt', 
}

# --- أوامر البوت ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = """
أهلاً بك يا صديقي! 👋
أنا بوت لتحميل الفيديوهات من أغلب منصات التواصل الاجتماعي (يوتيوب، فيسبوك، إنستجرام، وغيرها).

✅ **فقط أرسل لي رابط الفيديو وسأقوم بتحميله لك.**

🔍 *قريباً: خدمة البحث عن الفيديوهات مباشرة.*
    """
    bot.reply_to(message, welcome_text)

# --- معالج الروابط (التحميل المباشر) - شغال تمام ✅ ---
def is_url(message):
    # دالة بسيطة للتأكد إن الرسالة فيها رابط
    return "http" in message.text

@bot.message_handler(func=is_url)
def handle_video_link(message):
    url = message.text
    chat_id = message.chat.id
    msg_wait = bot.reply_to(message, "⏳ جاري معالجة الرابط... لحظات من فضلك.")

    try:
        # محاولة استخراج معلومات الفيديو ورابط التحميل المباشر
        with yt_dlp.YoutubeDL(ydl_opts_base) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            video_url = info_dict.get('url', None)
            video_title = info_dict.get('title', 'فيديو بدون عنوان')
            
            if not video_url:
                bot.edit_message_text("❌ عذراً، لم أتمكن من استخراج رابط الفيديو المباشر.", chat_id, msg_wait.message_id)
                return

            bot.edit_message_text(f"✅ تم العثور على الفيديو: {video_title}\nجاري الإرسال...", chat_id, msg_wait.message_id)
            
            # إرسال الفيديو للمستخدم
            bot.send_video(chat_id, video_url, caption=f"🎬 تم التحميل بواسطة: @{bot.get_me().username}")
            bot.delete_message(chat_id, msg_wait.message_id)

    except Exception as e:
        # في حالة حدوث خطأ
        error_message = str(e)
        print(f"Error downloading link: {error_message}") # طباعة الخطأ في السجلات
        bot.edit_message_text("❌ حدث خطأ أثناء محاولة تحميل الفيديو. قد يكون الرابط غير مدعوم أو محمي.", chat_id, msg_wait.message_id)
        
        # إبلاغ الأدمن بالخطأ (اختياري)
        if ADMIN_ID:
             try:
                 bot.send_message(ADMIN_ID, f"🚨 خطأ في البوت:\nمستخدم: {message.from_user.first_name}\nرابط: {url}\nالخطأ: {error_message}")
             except:
                 pass


# --- معالج البحث (رسائل عادية ليست روابط) - ❌ يحتاج تصليح ---
@bot.message_handler(func=lambda message: not is_url(message))
def handle_search(message):
    # هذا الجزء هو الذي لا يعمل حالياً ويحتاج إلى إصلاح
    # سنقوم فقط بإرسال رسالة مؤقتة حتى نصلحه
    bot.reply_to(message, "🔍 خدمة البحث قيد الصيانة حالياً، سيتم تفعيلها قريباً جداً! \nالرجاء إرسال روابط مباشرة فقط الآن.")
    
    # (هنا كان المفروض يكون كود البحث اللي بيسبب المشكلة)
    # print(f"Search attempt for: {message.text}")


# --- تشغيل البوت ---

# تشغيل سيرفر الـ Flask في الخلفية
keep_alive()

# تشغيل البوت في حلقة لا نهائية (Polling)
print("✅ البوت يعمل الآن...")
while True:
    try:
        bot.polling(none_stop=True, interval=0, timeout=20)
    except Exception as e:
        print(f"⚠️ حدث خطأ في الاتصال (Polling Error): {e}")

        time.sleep(5) # انتظار 5 ثواني قبل إعادة المحاولة

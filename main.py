 ✅ المنطق الطبيعي (Correct Logic):

# المفروض: الأولوية للي هينتهي الأول
def consume_data(daily_pkg, weekly_pkg):
    today = datetime.now()
    
    # لو الباقة اليومية هتخلص النهاردة.. اسحب منها فوراً
    if daily_pkg.expiry_date == today:
        user.consume(daily_pkg)
        print("لحقنا الباقة قبل ما تضيع!")
        
    elif weekly_pkg.is_active():
        user.consume(weekly_pkg)



❌ منطق الشركة (Orange Logic):

# الواقع: سيب اللي هيموت، واقتل اللي لسه عايش
def orange_billing_system(daily_pkg, weekly_pkg):
    # الباقة اليومية هتتحرق بكرة؟ طز فيها (Pass)
    # اسحب من الباقة الأسبوعية الغالية عشان تخلص بدري
    
    if weekly_pkg.has_quota():
        user.consume(weekly_pkg) # اسحب من الأسبوعية
        # وسيب اليومية (daily_pkg) تموت بمرور الوقت
        

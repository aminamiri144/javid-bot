import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from PIL import Image, ImageDraw, ImageFont
import io
import arabic_reshaper
from bidi.algorithm import get_display

# توکن ربات تلگرام - باید از @BotFather دریافت کنید
BOT_TOKEN = os.getenv("BOT_TOKEN", "8550969476:AAFOqTCzfYuVLJlypzAu52K_W_1ygzF-yEk")
# مسیر تصاویر دعوت‌نامه
MALE_INVITATION_IMAGE = "invitation_male.JPG"
FEMALE_INVITATION_IMAGE = "invitation_female.JPG"

# حالت‌های مکالمه
SELECTING_GENDER, GETTING_NAME = range(2)

# موقعیت و تنظیمات متن روی تصویر
TEXT_POSITION = {
    'male': (800, 1198),  # موقعیت X, Y برای آقایان
    'female': (800, 1198)  # موقعیت X, Y برای خانم‌ها
}

TEXT_COLOR = (255, 215, 0)  # رنگ طلایی
FONT_SIZE = 52

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """شروع ربات و نمایش دکمه‌های انتخاب جنسیت"""
    keyboard = [
        [InlineKeyboardButton("آقا", callback_data='male')],
        [InlineKeyboardButton("خانم", callback_data='female')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "جنسیت را انتخاب کنید:",
        reply_markup=reply_markup
    )
    
    return SELECTING_GENDER

async def gender_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """ذخیره جنسیت انتخاب شده و درخواست نام"""
    query = update.callback_query
    await query.answer()
    
    gender = query.data
    context.user_data['gender'] = gender
    
    await query.edit_message_text("لطفاً نام و نام خانوادگی خود را وارد کنید:")
    
    return GETTING_NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """دریافت نام و نام خانوادگی و ایجاد تصویر نهایی"""
    name = update.message.text.strip()
    
    if not name:
        await update.message.reply_text("لطفاً نام و نام خانوادگی خود را وارد کنید:")
        return GETTING_NAME
    
    context.user_data['name'] = name
    gender = context.user_data.get('gender')
    
    # انتخاب تصویر مناسب
    if gender == 'male':
        image_path = MALE_INVITATION_IMAGE
        position = TEXT_POSITION['male']
    else:
        image_path = FEMALE_INVITATION_IMAGE
        position = TEXT_POSITION['female']
    
    # بررسی وجود تصویر
    if not os.path.exists(image_path):
        await update.message.reply_text(f"خطا: تصویر {image_path} یافت نشد!")
        return ConversationHandler.END
    
    # نوشتن نام روی تصویر
    try:
        output_image = add_text_to_image(image_path, name, position)
        
        # ارسال تصویر
        await update.message.reply_photo(
            photo=output_image,
            caption=f"دعوت‌نامه {name}"
        )
        
        # نمایش دکمه برای ساخت دعوت‌نامه جدید
        keyboard = [
            [InlineKeyboardButton("ساخت دعوت‌نامه جدید", callback_data='new_invitation')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "آیا می‌خواهید دعوت‌نامه دیگری بسازید؟",
            reply_markup=reply_markup
        )
        
    except Exception as e:
        await update.message.reply_text(f"خطا در پردازش تصویر: {str(e)}")
    
    # پاک کردن داده‌های کاربر
    context.user_data.clear()
    
    return ConversationHandler.END

async def new_invitation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """شروع ساخت دعوت‌نامه جدید"""
    query = update.callback_query
    await query.answer()
    
    # نمایش دکمه‌های انتخاب جنسیت
    keyboard = [
        [InlineKeyboardButton("آقا", callback_data='male')],
        [InlineKeyboardButton("خانم", callback_data='female')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "جنسیت را انتخاب کنید:",
        reply_markup=reply_markup
    )
    
    return SELECTING_GENDER

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """لغو عملیات"""
    await update.message.reply_text("عملیات لغو شد.")
    context.user_data.clear()
    return ConversationHandler.END

def add_text_to_image(image_path: str, text: str, position: tuple) -> io.BytesIO:
    """نوشتن متن روی تصویر و برگرداندن تصویر به صورت BytesIO"""
    # باز کردن تصویر
    img = Image.open(image_path)
    draw = ImageDraw.Draw(img)
    
    # تلاش برای استفاده از فونت فارسی
    try:
        # استفاده از فونت پیش‌فرض سیستم یا فونت فارسی
        font_paths = [
            "fonts/Peyda-Black.ttf",  # فونت پایدا
            "fonts/Vazir.ttf",  # فونت وزیر
            "fonts/Shabnam.ttf",  # فونت شبنم
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # فونت لینوکس
        ]
        
        font = None
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    font = ImageFont.truetype(font_path, FONT_SIZE)
                    break
                except:
                    continue
        
        if font is None:
            # استفاده از فونت پیش‌فرض
            font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()
    
    # تبدیل متن فارسی برای نمایش صحیح
    try:
        # reshape کردن متن فارسی برای اتصال حروف
        reshaped_text = arabic_reshaper.reshape(text)
        # اصلاح جهت متن (RTL)
        bidi_text = get_display(reshaped_text)
    except:
        # در صورت خطا، از متن اصلی استفاده می‌شود
        bidi_text = text
    
    # نوشتن متن روی تصویر
    draw.text(position, bidi_text, fill=TEXT_COLOR, font=font)
    
    # تبدیل به BytesIO برای ارسال
    output = io.BytesIO()
    img.save(output, format='JPEG', quality=95)
    output.seek(0)
    
    return output

def main():
    """تابع اصلی برای راه‌اندازی ربات"""
    # ایجاد اپلیکیشن
    application = Application.builder().token(BOT_TOKEN).build()
    
    # ایجاد ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start), CallbackQueryHandler(new_invitation, pattern='^new_invitation$')],
        states={
            SELECTING_GENDER: [CallbackQueryHandler(gender_selected)],
            GETTING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    # اضافه کردن handler
    application.add_handler(conv_handler)
    
    # شروع ربات
    print("ربات در حال اجرا است...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()


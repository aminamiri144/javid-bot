import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from PIL import Image, ImageDraw, ImageFont
import io

# توکن ربات تلگرام - باید از @BotFather دریافت کنید
BOT_TOKEN = os.getenv("BOT_TOKEN", "8550969476:AAFOqTCzfYuVLJlypzAu52K_W_1ygzF-yEk")
# مسیر تصاویر دعوت‌نامه
MALE_INVITATION_IMAGE = "invitation_male.jpg"
FEMALE_INVITATION_IMAGE = "invitation_female.jpg"

# حالت‌های مکالمه
SELECTING_GENDER, GETTING_NAME = range(2)

# موقعیت و تنظیمات متن روی تصویر
TEXT_POSITION = {
    'male': (100, 400),  # موقعیت X, Y برای آقایان
    'female': (100, 400)  # موقعیت X, Y برای خانم‌ها
}

TEXT_COLOR = (255, 255, 255)  # رنگ سفید
FONT_SIZE = 48

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
            caption=f"دعوت‌نامه شما آماده است، {name} عزیز!"
        )
        
    except Exception as e:
        await update.message.reply_text(f"خطا در پردازش تصویر: {str(e)}")
    
    # پاک کردن داده‌های کاربر
    context.user_data.clear()
    
    return ConversationHandler.END

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
            "fonts/Peyda-Black.ttf",  # فونت وزیر
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
    
    # نوشتن متن روی تصویر
    draw.text(position, text, fill=TEXT_COLOR, font=font)
    
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
        entry_points=[CommandHandler('start', start)],
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


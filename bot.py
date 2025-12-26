import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from PIL import Image, ImageDraw, ImageFont
import io
import arabic_reshaper
from bidi.algorithm import get_display

# توکن ربات تلگرام - باید از @BotFather دریافت کنید
BOT_TOKEN = os.getenv("BOT_TOKEN", "8550969476:AAFOqTCzfYuVLJlypzAu52K_W_1ygzF-yEk")

# تعریف جفت تصاویر دعوت‌نامه
# فرمت: {'key': {'name': 'نام نمایشی', 'male': 'مسیر فایل مرد', 'female': 'مسیر فایل زن', 'position': (x, y)}}
position = (970, 1200)

IMAGE_SETS = {
    'invitation': {
        'name': 'جاوید سازه',
        'male': 'posters/javid_m.JPG',
        'female': 'posters/javid_f.JPG',
        'position': position
    },
    'namara': {
        'name': 'آجر نما نمارا',
        'male': 'posters/namara_m.jpg',
        'female': 'posters/namara_f.jpg',
        'position': position
    },
    'set2': {
        'name': 'دایاوین',
        'male': 'posters/dayavin_m.jpg',
        'female': 'posters/dayavin_f.jpg',
        'position': position
    },
    'set3': {
        'name': 'اسانسور ایوان',
        'male': 'posters/evan_m.jpg',
        'female': 'posters/evan_f.jpg',
        'position': position
    },
    'set4': {
        'name': 'بازرگانی هاشمی',
        'male': 'posters/hashemi_m.jpg',
        'female': 'posters/hashemi_f.jpg',
        'position': position
    },
    'set5': {
        'name': 'گالری کاشی صباغیان',
        'male': 'posters/sabaghian_m.jpg',
        'female': 'posters/sabaghian_f.jpg',
        'position': position
    },
}

# حالت‌های مکالمه
SELECTING_IMAGE_SET, SELECTING_GENDER, GETTING_NAME = range(3)

TEXT_COLOR = (255, 255, 255)  # رنگ طلایی
FONT_SIZE = 42

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """شروع ربات و نمایش دکمه‌های انتخاب جفت تصویر"""
    # ساخت دکمه‌ها برای انتخاب جفت تصویر
    keyboard = []
    for key, image_set in IMAGE_SETS.items():
        keyboard.append([InlineKeyboardButton(image_set['name'], callback_data=f'imgset_{key}')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "لطفاً اسپانسر دعوت‌نامه را انتخاب کنید:",
        reply_markup=reply_markup
    )
    
    return SELECTING_IMAGE_SET

async def image_set_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """ذخیره جفت تصویر انتخاب شده و نمایش دکمه‌های انتخاب جنسیت"""
    query = update.callback_query
    await query.answer()
    
    # استخراج key از callback_data (imgset_namara -> namara)
    image_set_key = query.data.replace('imgset_', '')
    context.user_data['image_set'] = image_set_key
    
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
    image_set_key = context.user_data.get('image_set')
    
    # بررسی وجود image_set در context
    if not image_set_key or image_set_key not in IMAGE_SETS:
        await update.message.reply_text("خطا: جفت تصویر انتخاب نشده است!")
        return ConversationHandler.END
    
    # انتخاب تصویر مناسب
    image_set = IMAGE_SETS[image_set_key]
    if gender == 'male':
        image_path = image_set['male']
    else:
        image_path = image_set['female']
    
    position = image_set['position']
    
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
    
    # ساخت دکمه‌ها برای انتخاب جفت تصویر
    keyboard = []
    for key, image_set in IMAGE_SETS.items():
        keyboard.append([InlineKeyboardButton(image_set['name'], callback_data=f'imgset_{key}')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "لطفاً اسپانسر دعوت‌نامه را انتخاب کنید:",
        reply_markup=reply_markup
    )
    
    return SELECTING_IMAGE_SET

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
    
    # گرفتن ابعاد تصویر
    img_width, img_height = img.size
    
    # تلاش برای استفاده از فونت فارسی
    try:
        # استفاده از فونت پیش‌فرض سیستم یا فونت فارسی
        font_paths = [
            "fonts/YekanBakh-Regular.ttf",  # فونت یکانبخ
            "fonts/YekanBakh-Regular",  # بدون پسوند
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
    
    # محاسبه موقعیت مرکز افقی (X در وسط تصویر)
    center_x = img_width // 2
    # موقعیت عمودی از position tuple گرفته می‌شود
    y_position = position[1]
    
    # نوشتن متن روی تصویر با anchor "mm" برای مرکز کردن متن
    draw.text((center_x, y_position), bidi_text, fill=TEXT_COLOR, font=font, anchor="mm")
    
    # تبدیل به BytesIO برای ارسال
    output = io.BytesIO()
    img.save(output, format='JPEG')
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
            SELECTING_IMAGE_SET: [CallbackQueryHandler(image_set_selected, pattern='^imgset_')],
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


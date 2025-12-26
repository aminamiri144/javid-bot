import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from PIL import Image, ImageDraw, ImageFont
import io
import arabic_reshaper
from bidi.algorithm import get_display

# توکن ربات تلگرام - باید از @BotFather دریافت کنید
BOT_TOKEN = os.getenv("BOT_TOKEN", "8550969476:AAFOqTCzfYuVLJlypzAu52K_W_1ygzF-yEk")

# تعریف تصاویر دعوت‌نامه
# فرمت: {'key': {'name': 'نام نمایشی', 'image': 'مسیر فایل تصویر', 'name_position': (x, y), 'signature_position': (x, y)}}

IMAGE = 'main_poster.JPG'
name_position = (970, 1200)
signature_position = (970, 2000)

IMAGE_SETS = {
    'invitation': {
        'name': 'گروه مهندسی جاوید سازه',
        'image': IMAGE,
        'name_position': name_position,
        'signature_position': signature_position
    },
    'namara': {
        'name': 'آجر نمای نمارا',
        'image': IMAGE,
        'name_position': name_position,
        'signature_position': signature_position
    },
    'set2': {
        'name': 'دایاوین',
        'image': IMAGE,
        'name_position': name_position,
        'signature_position': signature_position
    },
    'set3': {
        'name': 'آسانسور ایوان',
        'image': IMAGE,
        'name_position': name_position,
        'signature_position': signature_position
    },
    'set4': {
        'name': 'بازرگانی هاشمی',
        'image': IMAGE,
        'name_position': name_position,
        'signature_position': signature_position
    },
    'set5': {
        'name': 'گالری کاشی صباغیان',
        'image': IMAGE,
        'name_position': name_position,
        'signature_position': signature_position
    },
}


# حالت‌های مکالمه
SELECTING_IMAGE_SET, SELECTING_GENDER, GETTING_NAME = range(3)

TEXT_COLOR = (255, 255, 255)  # رنگ سفید
FONT_SIZE = 42
SIGNATURE_FONT_SIZE = 42

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
    """ذخیره تصویر انتخاب شده و نمایش دکمه‌های انتخاب جنسیت"""
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
        await update.message.reply_text("خطا: تصویر انتخاب نشده است!")
        return ConversationHandler.END
    
    # انتخاب تصویر
    image_set = IMAGE_SETS[image_set_key]
    image_path = image_set['image']
    
    # بررسی وجود تصویر
    if not os.path.exists(image_path):
        await update.message.reply_text(f"خطا: تصویر {image_path} یافت نشد!")
        return ConversationHandler.END
    
    # ساخت متن نام با پیشوند مناسب
    if gender == 'male':
        full_name_text = f"جناب آقای {name}"
    else:
        full_name_text = f"سرکار خانم {name}"

    # نوشتن متن روی تصویر
    try:
        output_image = add_text_to_image(
            image_path, 
            full_name_text, 
            image_set['name'],
            image_set['name_position'],
            image_set['signature_position']
        )
        
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

def get_font(font_size: int):
    """دریافت فونت با اندازه مشخص"""
    font_paths = [
        "fonts/YekanBakhFaNum-SemiBold.ttf",
        "fonts/YekanBakhFaNum-SemiBold",
    ]
    
    font = None
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                font = ImageFont.truetype(font_path, font_size)
                break
            except:
                continue
    
    if font is None:
        font = ImageFont.load_default()
    
    return font

def process_persian_text(text: str) -> str:
    """تبدیل متن فارسی برای نمایش صحیح"""
    try:
        reshaped_text = arabic_reshaper.reshape(text)
        bidi_text = get_display(reshaped_text)
        return bidi_text
    except:
        return text

def add_text_to_image(image_path: str, name_text: str, sponsor_name: str, name_position: tuple, signature_position: tuple) -> io.BytesIO:
    """نوشتن دو متن روی تصویر: نام و امضا"""
    # باز کردن تصویر
    img = Image.open(image_path)
    draw = ImageDraw.Draw(img)
    
    # دریافت فونت‌ها
    name_font = get_font(FONT_SIZE)
    signature_font = get_font(SIGNATURE_FONT_SIZE)
    
    # تبدیل متن فارسی برای نام
    name_bidi = process_persian_text(name_text)
    
    # محاسبه موقعیت برای نام
    name_x = name_position[0]
    name_y = name_position[1]
    
    # نوشتن متن نام روی تصویر با anchor "rt" برای راست‌چین کردن
    draw.text((name_x, name_y), name_bidi, fill=TEXT_COLOR, font=name_font, anchor="rt")
    
    # ساخت متن امضا: "با احترام / نام اسپانسر"
    signature_text = f"با احترام / {sponsor_name}"
    
    # تبدیل متن فارسی برای امضا
    signature_bidi = process_persian_text(signature_text)
    
    # محاسبه موقعیت برای امضا
    signature_x = signature_position[0]
    signature_y = signature_position[1]
    
    # نوشتن متن امضا روی تصویر با anchor "rt" برای راست‌چین کردن
    draw.text((signature_x, signature_y), signature_bidi, fill=TEXT_COLOR, font=signature_font, anchor="rt")
    
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


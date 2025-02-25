import os
import django
from telegram import (
    Update,
    InlineKeyboardMarkup, 
    InlineKeyboardButton,
    InputFile,
    )
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackContext,
    filters,
    CallbackQueryHandler,
    JobQueue,
)
from datetime import datetime, time
from pytz import timezone

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "studio100.settings"
)

django.setup()

# importing models and needed modules from django.
from django.db import transaction
from django.db.models import F
from admin_panel.models import user_data, price, Video
from checkout.models import invoices

CHANNEL_ID = os.getenv("CHANNEL_ID")
CHANNEL_ID = "@studio100_test"  # Use the channel username or ID (e.g., -1001234567890)



async def start(update: Update, context: CallbackContext):
    # updating user info from telegram
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name or ""
    last_name = update.effective_user.last_name or ""
    username = update.effective_user.username or ""

    try:
        existing_user = await user_data.objects.aget(id=user_id)
        await update.message.reply_text(f"خوش برگشتی {existing_user.first_name}!")

    except user_data.DoesNotExist:
        # If the user does not exist, create a new entry
        new_user = user_data(
            id=user_id,
            first_name=first_name,
            last_name=last_name,
            username=username,
            remaining_days=0,
            number=0,
        )
        await new_user.asave()
        await update.message.reply_text(" خوش آمدید! لطفا شماره خود را تنظیم کنید.")
        print(
            f"[record--status:successful] - time: {datetime.now(tz=timezone('asia/tehran'))} -- Info:new user added to bot, id: {user_id}"
        )
        context.user_data['awaiting_number'] = True  # Await number input
        await update.message.reply_text("لطفا شماره خود را وارد کنید:")



async def texts_handler(update: Update, context: CallbackContext):
    user_id = update.effective_user.id  # Get the user ID
    user_message = (
        update.message.text if update.message.text else "(No text)"
    )  # Fallback for no text
    user = await user_data.objects.aget(id=user_id)
    
    if context.user_data.get('awaiting_name'):
        new_name = update.message.text
        user.first_name = new_name
        await user.asave()
        await update.message.reply_text(f"نام شما به {new_name} تغییر یافت.")
        context.user_data['awaiting_name'] = False  # Reset flag
        return  # Exit the function to prevent further processing
        
    elif context.user_data.get('awaiting_number'):
        new_number = update.message.text
        if new_number.isdigit():
            user.number = int(new_number)
            await user.asave()
            await update.message.reply_text(f"شماره شما به {new_number} تغییر یافت.")
            context.user_data['awaiting_number'] = False  # Reset flag
            if not(user.first_name):
                await update.message.reply_text(f"لطفا نام خود را وارد کنید:")
                context.user_data['awaiting_name'] = True  # Reset flag
            return  # Exit the function to prevent further processing
        else:
            await update.message.reply_text("لطفا یک شماره معتبر وارد کنید.")
        return  # Exit the function to prevent further processing
    
async def show_days(update: Update, context: CallbackContext):
    '''
    Shows tokens in telegram bot with /token command.
    Also provides 3 options to increase tokens.
    '''
    
    # Create inline buttons for purchase options
    keyboard = []
    
    for i in range(1, 3):
        try:
            # Fetch token option asynchronously
            token_option = await price.objects.aget(option=i)
            # Create a button with the token price and add to keyboard
            keyboard.append([
                InlineKeyboardButton(
                    f"{token_option.price} ریال ",
                    callback_data=f"option_purchase_{i}"
                )
            ])
        except:
            # Skip this option if it doesn't exist
            print(f"Option {i} does not exist in the database.")
            continue
        
    # Create reply markup with inline keyboard
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Fetch user data asynchronously
    user_id = update.effective_user.id
    user = await user_data.objects.aget(id=user_id)
    
    # Send reply with token balance and purchase options
    await update.message.reply_text(
        f"تعداد روزهای باقیمانده: {user.remaining_days}. برای افزایش سابسکریپشن یکی از گزینه های زیر را انتخاب کنید:",
        reply_markup=reply_markup,
    )

async def user_purchase_verifing(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = update.effective_user.id
    await query.answer()  # Acknowledge the callback
    user = await user_data.objects.aget(id=user_id)
    keyboard = [
        [
            InlineKeyboardButton("لغو", callback_data="option_finalize_0"),
        ]
    ]
    if query.data == "option_purchase_1":
        token_option = await price.objects.aget(option=1)
        keyboard[0].append(
            InlineKeyboardButton("تایید", callback_data="option_finalize_1"),
        )
    elif query.data == 'option_purchase_2': 
        token_option = await price.objects.aget(option=2)
        keyboard[0].append(
            InlineKeyboardButton("تایید", callback_data="option_finalize_2"),
        )
    replay_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text=f"تعداد روزهای های دریافتی: {token_option.days} ایا تایید میکنید؟", reply_markup=replay_markup
    )
    
async def purchase_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = update.effective_user.id
    await query.answer()  # Acknowledge the callback
    user = await user_data.objects.aget(id=user_id)
    website = os.getenv("WEBSITE_URL")
    if query.data == "option_finalize_1":
        token_option = await price.objects.aget(option=1)
        new_invoice = invoices(
            user_id = user,
            amount = token_option.price,
            status = "HOLD"
        )
        await new_invoice.asave()
        purchase_link = f"{website}/checkout/request/{new_invoice.id}"
        await query.edit_message_text(
            text=f"برای تکمیل خرید از طریق این لینک اقدام کنید: {purchase_link}"
        )
        
        print(
            f"[record--status:successful] - time: {datetime.now(tz=timezone('asia/tehran'))} -- Info: user: {user_id}, added a new invoice."
        )
    elif query.data == "option_finalize_2":
        token_option = await price.objects.aget(option=2)
        new_invoice = invoices(
            user_id = user,
            amount = token_option.price,
            status = "HOLD"
        )
        await new_invoice.asave()
        purchase_link = f"{website}/checkout/request/{new_invoice.id}"
        await query.edit_message_text(
            text=f"برای تکمیل خرید از طریق این لینک اقدام کنید: {purchase_link}"
        )
        print(
            f"[record--status:successful] - time: {datetime.now(tz=timezone('asia/tehran'))} -- Info: user: {user_id}, added a new invoice."
        )
    elif query.data == 'option_finalize_0':
        await query.edit_message_text(
            text='درخواست شما لغو شد.'
        )

    
async def change_user_info(update: Update, context: CallbackContext):
    # Create inline buttons for model options
    keyboard = [
        [
            InlineKeyboardButton("نام", callback_data="change_user_name"),
            InlineKeyboardButton("شماره", callback_data="change_user_number"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Display the model selection buttons
    await update.message.reply_text(
        "برای تغییر نام یا شماره تماس خود کلیک کنید:",
        reply_markup=reply_markup,
    )
    
async def change_name(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()  # Acknowledge the callback
    
    # Prompt the user to enter their new name
    await query.edit_message_text("لطفا نام جدید خود را ارسال کنید:")
    
    # Set the context for tracking the next user message as their new name
    context.user_data['awaiting_name'] = True
    
async def change_number(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()  # Acknowledge the callback
    
    # Prompt the user to enter their new name
    await query.edit_message_text("لطفا شماره جدید خود را ارسال کنید:")
    
    # Set the context for tracking the next user message as their new name
    context.user_data['awaiting_number'] = True

async def check_user_subscription(context: CallbackContext):
    print(f"[record--status:start] - time: {datetime.now(tz=timezone('Asia/Tehran'))} -- Info: Daily subscription check started")

    # Get users with remaining days
    async for user in user_data.objects.filter(remaining_days__gt=0):
        user.remaining_days -= 1
        await user.asave()
    
    print(f"[record--status:successful] - time: {datetime.now(tz=timezone('Asia/Tehran'))} -- Info: Remaining days decremented for all users")

    # Get and process expired users
    async for user in user_data.objects.filter(remaining_days=0):
        try:
            await context.bot.ban_chat_member(CHANNEL_ID, user_id=user.id)
            print(f"[record--action:kick] - time: {datetime.now(tz=timezone('Asia/Tehran'))} -- Info: User {user.id} kicked from the channel")
        except Exception as e:
            print(f"[record--error] - time: {datetime.now(tz=timezone('Asia/Tehran'))} -- Error kicking user {user.id}: {e}")

async def get_video(update: Update, context: CallbackContext):
    """
    Fetches the most recent video uploaded via the admin panel
    and sends it to the user.
    """
    try:
        # Get the latest uploaded video
        video = await Video.objects.all().order_by('-uploaded_at').afirst()
        if video:
            video_path = video.video_file.path
            # Sending the video using its file path. Make sure your MEDIA_ROOT is accessible.
            await update.message.reply_video(
                video=InputFile(open(video_path, 'rb')),
                caption=video.title
            )
        else:
            await update.message.reply_text("هیچ ویدیویی یافت نشد.")
    except Exception as e:
        print(f"[record--error] Error in get_video: {e}")
        await update.message.reply_text("مشکلی در ارسال ویدیو به وجود آمد.")

# New Function 2: Provide Premium Link if User Has Active Subscription
async def get_premium_link(update: Update, context: CallbackContext):
    """
    Checks if the user has remaining subscription days.
    If so, sends them a premium link; otherwise, notifies them that their subscription is inactive.
    """
    user_id = update.effective_user.id
    try:
        user = await user_data.objects.aget(id=user_id)
        if user.remaining_days > 0:
            # Replace the below link with the actual destination
            # premium_link = "http://your-premium-content.example.com"
            await update.message.reply_text(
                f"اشتراک شما فعال است. برای دسترسی به محتوا از این لینک استفاده کنید: {CHANNEL_ID}"
            )
        else:
            await update.message.reply_text("متاسفانه اشتراک شما منقضی شده است.")
    except user_data.DoesNotExist:
        await update.message.reply_text("کاربر یافت نشد. لطفا ابتدا با دستور /start ثبت نام کنید.")

def main():
    print(
        f"[record--status:start] - time: {datetime.now(tz=timezone('Asia/Tehran'))} -- Info: bot started."
    )
    token = os.getenv("TOKEN")
    print(token)
    # Set up the application (bot) using the latest python-telegram-bot version
    application = Application.builder().token(token).build()

    # Add command and message handlers
    application.add_handler(CommandHandler("start", start))

    application.add_handler(CommandHandler("editinfo", change_user_info))
    application.add_handler(CallbackQueryHandler(change_name, pattern="change_user_name"))
    application.add_handler(CallbackQueryHandler(change_number, pattern="change_user_number"))

    application.add_handler(CommandHandler("subscription", show_days))
    application.add_handler(CallbackQueryHandler(user_purchase_verifing ,pattern="^option_purchase"))
    application.add_handler(CallbackQueryHandler(purchase_handler, pattern="^option_finalize"))
   
    application.add_handler(CommandHandler("video", get_video))
    application.add_handler(CommandHandler("getlink", get_premium_link))

    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, texts_handler)
    )

    # Set up the job queue before polling starts
    job_queue = application.job_queue

    # Schedule daily subscription check at 9:00 AM Tehran time
    job_queue.run_daily(check_user_subscription, time=time(hour=12, minute=30, tzinfo=timezone('Asia/Tehran'))
    )
    print(f"[record--status:successful] - time: {datetime.now(tz=timezone('Asia/Tehran'))} -- Info: Scheduled jobs: {job_queue.jobs()}")


    # Start the bot
    application.run_polling()

    
if __name__ == "__main__":
    main()
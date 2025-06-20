import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, File

# You can get the bot token at https://t.me/BotFather
# IMPORTANT: specify your token
TOKEN = "7639600747:AAFHYYs9M_ji9I83IPTD2VsM8VoYidxkRmk"

dp = Dispatcher()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}!")


@dp.message()
async def echo_handler(message: Message) -> None:
    # Check if the message contains a photo
    if message.photo:
        # Get the largest photo (highest resolution)
        photo = message.photo[-1]
        file_info = await message.bot.get_file(photo.file_id)
        file_path = file_info.file_path
        # Download the photo
        file = await message.bot.download_file(file_path)
        # Save the photo to the images directory
        image_dir = "images"
        os.makedirs(image_dir, exist_ok=True)
        image_path = os.path.join(image_dir, f"{photo.file_id}.jpg")
        with open(image_path, "wb") as f:
            f.write(file.read())
        await message.answer("I got the image!")
    else:
        try:
            # Send a copy of the received message
            await message.send_copy(chat_id=message.chat.id)
        except TypeError:
            # But not all types support copying, so handle this
            await message.answer("Nice try!")


async def main() -> None:
    # Initialize the bot instance with default properties that will be passed to all API calls
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # Start event processing
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
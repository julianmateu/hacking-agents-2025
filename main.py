import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, File
import requests

# You can get the bot token at https://t.me/BotFather
# IMPORTANT: specify your token
from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv('TOKEN')
LANGFLOW_TOKEN = os.getenv('LANGFLOW_TOKEN')
LANGFLOW_URL =  os.getenv('LANGFLOW_URL')
dp = Dispatcher()

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}!")


def call_langflow_flow(input_text: str) -> str:
    payload = {
        "input_value": str(input_text),
        "output_type": "chat",
        "input_type": "chat"
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LANGFLOW_TOKEN}"
    }

    try:
        response = requests.post(LANGFLOW_URL, json=payload, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        return f"Error making API request: {e}"
    except ValueError as e:
        return f"Error parsing response: {e}"


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
        await message.answer("Hey! Thanks for reaching to InteriorAi, I've recieved your image and I'm just about to start putting together some furniture ideas that suit your space. Please wait a moment...")
        response = call_langflow_flow(f"Chat id is {message.chat.id}")

        eleven_labs_url = response['eleven_labs_url']
        ## Reply to the user so they start a conversation with this URL
        await message.answer(f"I've started working on your request. You can continue the conversation here: {eleven_labs_url}")

    elif message.text and "test_id" in message.text.lower():
        ## Extract conversation ID from the message text
        lower_text = message.chat.id
        # lets reply with the chat id
        await message.answer(f"Your chat ID is: {lower_text}")
    elif message.text and "connect" in message.text.lower():
        # Extract everything after 'connect'
        lower_text = message.text.lower()
        idx = lower_text.find("connect")
        # Get the original text after 'connect' (preserving case)
        after_connect = message.text[idx + len("connect"):].strip()
        if after_connect:
            response = call_langflow_flow(f"Chat id is {message.chat.id}")
            if response.startswith("SEND_IMAGE:"):
                image_path = response[len("SEND_IMAGE:"):].strip()
                if os.path.exists(image_path):
                    with open(image_path, "rb") as img_file:
                        await message.answer_photo(img_file)
                else:
                    await message.answer(f"Image not found: {image_path}")
            # else:
            #     await message.answer(response)
        else:
            await message.answer("Please provide text after 'connect'.")
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

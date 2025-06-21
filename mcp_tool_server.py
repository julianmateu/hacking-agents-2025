# mcp_tool_server.py
"""
A minimal MCP server exposing a tool for Langflow.
"""

from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import Any
import uvicorn
import json
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

import os
import asyncio
import requests
import logging

from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

class GenerateImageInput(BaseModel):
    chat_id: str

class GenerateImageOutput(BaseModel):
    result: str

# Configure logging
logging.basicConfig(level=logging.INFO)

OPENAI_IMAGE_CACHE = "images/bedroom_couch_pillow_response.json"
OPENAI_IMAGE_RESULT = "images/bedroom_couch_pillow.png"

SYSTEM_PROMPT = (
    "I want you to generate an EXACT version of how this bedroom would look like with this couch and pillow in it. "
    "Please use the same designs and do not alter the objects."
)


def generate_openai_image():
    """
    Calls OpenAI image API to generate an image, caches the result, and returns the image path.
    If the cache exists, loads from cache instead of calling OpenAI.
    """
    import requests
    import os
    import json

    if os.path.exists(OPENAI_IMAGE_CACHE) and os.path.exists(OPENAI_IMAGE_RESULT):
        logging.info(f"Cache found at {OPENAI_IMAGE_CACHE}, loading cached image.")
        return OPENAI_IMAGE_RESULT

    logging.info("No cache found, calling OpenAI image API...")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        logging.error("OPENAI_API_KEY not set in environment.")
        raise RuntimeError("OPENAI_API_KEY not set.")

    url = "https://api.openai.com/v1/images/edits"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    files = [
        ("model", (None, "gpt-image-1")),
        ("image[]", ("bedroom.jpg", open("images/bedroom.jpg", "rb"), "image/jpeg")),
        ("image[]", ("couch.jpg", open("images/couch.jpg", "rb"), "image/jpeg")),
        ("image[]", ("pillow.jpg", open("images/pillow.jpg", "rb"), "image/jpeg")),
        ("prompt", (None, SYSTEM_PROMPT)),
    ]
    logging.info("Sending request to OpenAI...")
    response = requests.post(url, headers=headers, files=files)
    logging.info(f"OpenAI response status: {response.status_code}")
    if response.status_code != 200:
        logging.error(f"OpenAI API error: {response.text}")
        raise RuntimeError(f"OpenAI API error: {response.text}")

    # Save response to cache
    with open(OPENAI_IMAGE_CACHE, "w") as f:
        f.write(response.text)
    logging.info(f"Response cached at {OPENAI_IMAGE_CACHE}")

    # Extract and save image
    data = response.json()
    b64 = data["data"][0]["b64_json"]
    import base64
    with open(OPENAI_IMAGE_RESULT, "wb") as imgf:
        imgf.write(base64.b64decode(b64))
    logging.info(f"Image saved at {OPENAI_IMAGE_RESULT}")
    return OPENAI_IMAGE_RESULT



@app.post("/generate_image")
async def generate_image_endpoint(request: Request):
    print("Received request to /generate_image endpoint.")
    logging.info("/generate_image endpoint called.")
    string_request = await request.body()
    data = json.loads(string_request.decode('utf-8').replace("\\", ""))
    chat_id = data.get("chat_id") or data.get("input")
    # Extract optional items array
    items = data.get("items", [])
    logging.info(f"Extracted chat_id: {chat_id}")
    logging.info(f"Extracted items: {items}")
    if not chat_id:
        logging.error("Missing 'chat_id' or 'input' in request.")
        return {"error": "Missing 'chat_id' or 'input' in request."}
    TOKEN = os.getenv('TOKEN')
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    ## Generate text expaining the furniture items
    items_description = ""
    if items:
        items_description = "Here are the furniture items I found for you:\n"
        for item in items:
            # item_desc = json.
            items_description += f"- {item["name"], item['buy_url']}\n"
    else:
        items_description = "I couldn't find any specific furniture items, but I can still help you visualize your space."
    logging.info(f"Items description: {items_description}")
    # Send a message to the chat with the items description
    try:
        await bot.send_message(chat_id=chat_id, text=items_description)
    except Exception as e:
        logging.error(f"Failed to send message to chat {chat_id}: {e}")
        return {"error": str(e)}

    # Generate or load image
    try:
        image_path = generate_openai_image()
    except Exception as e:
        logging.error(f"Image generation failed: {e}")
        return {"error": str(e)}

    files = {'photo': open(image_path, 'rb')}
    status = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto?chat_id=" + str(chat_id), files=files)
    logging.info(f"Telegram sendPhoto status: {status.status_code}")
    return GenerateImageOutput(result=f"Image sent to chat {chat_id}")

if __name__ == "__main__":
    uvicorn.run("mcp_tool_server:app", host="0.0.0.0", port=8000, reload=True)

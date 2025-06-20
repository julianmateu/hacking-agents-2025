# Hacking Agents Hackathon 2025

To run langflow using docker:
```bash
docker-compose up -d
```

## Telegram Bot Image Saving

This project includes a Telegram bot using aiogram. When a user sends an image to the bot, it will be saved in the `images` folder and the bot will reply with "I got the image!". Other messages will be echoed back.

### Running the Bot

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the bot:
   ```bash
   python main.py
   ```

### Image Storage
- Images sent to the bot are saved in the `images` directory with their file ID as the filename.

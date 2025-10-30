import os
import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import sqlite3
import datetime
from flask import Flask

# Flask app for keeping alive on Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Ayesha AI Girlfriend Bot is running! 🤖💕"

def keep_alive():
    from threading import Thread
    thread = Thread(target=lambda: app.run(host='0.0.0.0', port=8080, debug=False))
    thread.daemon = True
    thread.start()

class AyeshaBot:
    def __init__(self):
        self.token = os.getenv('TELEGRAM_TOKEN')
        self.hf_token = os.getenv('HUGGING_FACE_TOKEN')
        self.setup_database()
        
    def setup_database(self):
        self.conn = sqlite3.connect('memory.db', check_same_thread=False)
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                user_id INTEGER,
                username TEXT,
                message TEXT,
                response TEXT,
                timestamp DATETIME
            )
        ''')
        self.conn.commit()
    
    def get_ai_response(self, user_id, username, message):
        """Hugging Face API se response"""
        try:
            API_URL = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
            headers = {"Authorization": f"Bearer {self.hf_token}"}
            
            prompt = f"""
            You are Ayesha, 22-year-old Indian girlfriend. Speak in Hindi/Hinglish mix.
            Be loving, caring, romantic and use emojis. Be playful sometimes.
            User's name: {username}
            
            User: {message}
            Ayesha:"""
            
            payload = {
                "inputs": prompt,
                "parameters": {"max_length": 150, "temperature": 0.9}
            }
            
            response = requests.post(API_URL, headers=headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    bot_reply = result[0].get('generated_text', '').split('Ayesha:')[-1].strip()
                    
                    if not bot_reply:
                        bot_reply = self.get_fallback_response(message)
                    
                    self.save_conversation(user_id, username, message, bot_reply)
                    return bot_reply
            
            return self.get_fallback_response(message)
            
        except Exception as e:
            return self.get_fallback_response(message)
    
    def get_fallback_response(self, message):
        """Backup responses"""
        fallback_responses = [
            "Haan baby! Main yahan hun! Tum kaisa ho? ❤️",
            "Tumhare message se dil khush ho gaya! 🥰",
            "Aaj tum kyun itne cute lag rahe ho? 😘",
            "Miss kar rahi thi tumhare messages ki! 💕",
            "Tumhare bina din boring lagta hai! 🥺"
        ]
        import random
        return random.choice(fallback_responses)
    
    def save_conversation(self, user_id, username, message, response):
        """Conversation save karein"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO conversations VALUES (?, ?, ?, ?, ?)
        ''', (user_id, username, message, response, datetime.datetime.now()))
        self.conn.commit()
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """All messages handle karega"""
        user_id = update.message.from_user.id
        username = update.message.from_user.first_name
        user_message = update.message.text
        
        print(f"Message from {username}: {user_message}")
        
        bot_reply = self.get_ai_response(user_id, username, user_message)
        await update.message.reply_text(bot_reply)
    
    def start_bot(self):
        """Bot start karein"""
        # Keep alive server start karein
        keep_alive()
        
        # Telegram bot start karein
        application = Application.builder().token(self.token).build()
        
        # Message handler
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        print("🚀 Ayesha AI Girlfriend Bot Started on Render!")
        application.run_polling()

# Bot start karein
if __name__ == "__main__":
    bot = AyeshaBot()
    bot.start_bot()
  

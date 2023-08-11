# 6031866012:AAHqAix7aWBLLzk6NFQyHJhsttpeMf55Sbc
'''

Done! Congratulations on your new bot. You will find it at t.me/calesi_2023_bot. You can now add a description, about section and profile picture for your bot, see /help for a list of commands. By the way, when you've finished creating your cool bot, ping our Bot Support if you want a better username for it. Just make sure the bot is fully operational before you do this.

Use this token to access the HTTP API:
6031866012:AAHqAix7aWBLLzk6NFQyHJhsttpeMf55Sbc
Keep your token secure and store it safely, it can be used by anyone to control your bot.

For a description of the Bot API, see this page: https://core.telegram.org/bots/api

'''

import telebot
import requests

#BOT_TOKEN = os.environ.get('BOT_TOKEN')
BOT_TOKEN = '6031866012:AAHqAix7aWBLLzk6NFQyHJhsttpeMf55Sbc'
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    bot.reply_to(message, "Guenas, tudu bom bom?")

@bot.message_handler(commands=['horoscopo'])
def sign_handler(message):
    text = "Cual es tu signo?\nElige uno: *Aries*, *Taurus*, *Gemini*, *Cancer,* *Leo*, *Virgo*, *Libra*, *Scorpio*, *Sagittarius*, *Capricorn*, *Aquarius*, and *Pisces*."
    sent_msg = bot.send_message(message.chat.id, text, parse_mode="Markdown")
    bot.register_next_step_handler(sent_msg, day_handler)

#@bot.message_handler(func=lambda msg: True)
#def echo_all(message):
    #bot.reply_to(message, message.text)

def sendMessage(text):
    bot.send_message(text)

def get_daily_horoscope(sign: str, day: str) -> dict:
    """Get daily horoscope for a zodiac sign.
    Keyword arguments:
    sign:str - Zodiac sign
    day:str - Date in format (YYYY-MM-DD) OR TODAY OR TOMORROW OR YESTERDAY
    Return:dict - JSON data
    """
    url = "https://horoscope-app-api.vercel.app/api/v1/get-horoscope/daily"
    params = {"sign": sign, "day": day}
    response = requests.get(url, params)

    return response.json()

def day_handler(message):
    sign = message.text
    text = "Que día quieres conocer?\nElige uno: *TODAY*, *TOMORROW*, *YESTERDAY*, or a date in format YYYY-MM-DD."
    sent_msg = bot.send_message(
        message.chat.id, text, parse_mode="Markdown")
    bot.register_next_step_handler(
        sent_msg, fetch_horoscope, sign.capitalize())

def fetch_horoscope(message, sign):
    day = message.text
    horoscope = get_daily_horoscope(sign, day)
    data = horoscope["data"]
    horoscope_message = f'*Horoscopo:* {data["horoscope_data"]}\\n*Sign:* {sign}\\n*Day:* {data["date"]}'
    bot.send_message(message.chat.id, "Aquí está tu horóscopo!")
    bot.send_message(message.chat.id, horoscope_message, parse_mode="Markdown")

bot.infinity_polling()
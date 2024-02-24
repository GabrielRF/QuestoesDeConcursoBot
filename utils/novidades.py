import telebot
import os

bot = telebot.TeleBot(os.environ.get('BOT_TOKEN'))

message = (
    f'<b>Bot atualizado!</b>\n\n'
    f'{os.environ.get("commit_message")}'
)

bot.send_message(
    '@GabRF',
    message,
    reply_to_message_id=615,
    parse_mode='HTML'
)

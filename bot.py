import logging
import telebot # библиотека telebot
from telebot.types import Message
from config import token # импорт токена

class NoPermissionsError(Exception):
    pass

def ban(bot: telebot.TeleBot, message: Message) -> None:
    chat_id = message.chat.id # сохранение id чата
    user_id = message.from_user.id # сохранение id и статуса пользователя, отправившего сообщение
    user_status = bot.get_chat_member(chat_id, user_id).status 
    # проверка пользователя
    if user_status == 'administrator' or user_status == 'creator':
        raise NoPermissionsError("Невозможно забанить администратора!")
    else:
        bot.ban_chat_member(chat_id, user_id) # пользователь с user_id будет забанен в чате с chat_id
        

def main() -> None:
    bot = telebot.TeleBot(token) 

    @bot.message_handler(commands=['start'])
    def start(message: Message):
        bot.reply_to(message, "Привет! Я бот для управления чатом.")

    @bot.message_handler(commands=['ban'])
    def ban_user(message: Message):
        arguments = message.text.split(" ", 1)
        
        if len(arguments) == 1:
            reason = ""
        else:
            reason = arguments[1]

        if message.reply_to_message is None: 
            bot.reply_to(message, "Эта команда должна быть использована в ответ на сообщение пользователя, которого вы хотите забанить.")
            return
        
        try:
            ban(bot, message.reply_to_message)
        except NoPermissionsError as err:
            bot.reply_to(message, str(err))
            return
        
        bot.reply_to(message, f"Пользователь @{message.reply_to_message.from_user.username} был забанен.\nПричина: {reason!r}")

    @bot.message_handler(func=lambda message: "http://" in message.text or "https://" in message.text)
    def moderation(message: Message):
        try:
            ban(bot, message)
        except NoPermissionsError:
            return
        
        bot.reply_to(message, f"Пользователь @{message.from_user.username} был забанен.\nПричина: 'Реклама'")

    bot.infinity_polling(none_stop=True, logger_level=logging.DEBUG)


if __name__ == "__main__":
    main()
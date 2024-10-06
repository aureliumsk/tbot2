import logging
import telebot # библиотека telebot
from telebot.types import Message
from config import token # импорт токена


def main() -> None:
    bot = telebot.TeleBot(token) 

    @bot.message_handler(commands=['start'])
    def start(message: Message):
        bot.reply_to(message, "Привет! Я бот для управления чатом.")


    @bot.message_handler(commands=['ban'])
    def ban_user(message: Message):
        if not message.reply_to_message: 
            bot.reply_to(message, "Эта команда должна быть использована в ответ на сообщение пользователя, которого вы хотите забанить.")
            return
        chat_id = message.chat.id # сохранение id чата
        user_id = message.reply_to_message.from_user.id # сохранение id и статуса пользователя, отправившего сообщение
        user_status = bot.get_chat_member(chat_id, user_id).status 
        # проверка пользователя
        if user_status == 'administrator' or user_status == 'creator':
            bot.reply_to(message, "Невозможно забанить администратора.")
        else:
            bot.ban_chat_member(chat_id, user_id) # пользователь с user_id будет забанен в чате с chat_id
            bot.reply_to(message, f"Пользователь @{message.reply_to_message.from_user.username} был забанен.")


    bot.infinity_polling(none_stop=True, logger_level=logging.DEBUG)


if __name__ == "__main__":
    main()
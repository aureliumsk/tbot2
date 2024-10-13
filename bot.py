import logging
import telebot # библиотека telebot
from telebot.types import Message
from config import token # импорт токена

WARN_LIMIT = 3
MESSAGES = (
    "Пользователь @{} был забанен.\nПричина: {!r}",
    "Пользователю @{} выдано предупреждение ({} из %d).\nПричина: {!r}" % (WARN_LIMIT),
    "Невозможно забанить администратора!",
    "Невозможно выдать предупреждение администратору!"
)

class BotMessage:
    def __init__(self, type: int, string: str | None = None) -> None:
        self.type = type
        self.string = string or MESSAGES[type]
    
    def __eq__(self, other):
        if isinstance(other, BotMessage):
            return self.type == other.type
        return NotImplemented

    def format(self, *args):
        return BotMessage(self.type, self.string.format(*args))


BAN_MESSAGE = BotMessage(0)
WARN_MESSAGE = BotMessage(1)
UNABLE_TO_BAN_MESSAGE = BotMessage(2)
UNABLE_TO_WARN_MESSAGE = BotMessage(3)


def ban(bot: telebot.TeleBot, message: Message, reason: str = "") -> BotMessage:
    chat_id = message.chat.id
    user_id = message.from_user.id
    user_status = bot.get_chat_member(chat_id, user_id).status 

    if user_status == 'administrator' or user_status == 'creator':
        return UNABLE_TO_BAN_MESSAGE
    
    bot.ban_chat_member(chat_id, user_id)

    return BAN_MESSAGE.format(message.from_user.username, reason)



def warn(bot: telebot.TeleBot, message: Message, reason: str = "") -> tuple[BotMessage, ...] | BotMessage:
    chat_id = message.chat.id
    user_id = message.from_user.id
    user_status = bot.get_chat_member(chat_id, user_id).status 

    if user_status == 'administrator' or user_status == 'creator':
        return UNABLE_TO_WARN_MESSAGE
    
    new_warn_count = bot.retrieve_data(user_id, chat_id).get("warn_count", 0) + 1
    bot.add_data(user_id, chat_id, warn_count=new_warn_count)

    success_message = WARN_MESSAGE.format(message.from_user.username, new_warn_count, reason)
    
    if new_warn_count > WARN_LIMIT:
        return success_message, ban(bot, message, "Превышение лимита предупреждений")
    else:
        return success_message





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
              
        bot.reply_to(message, ban(bot, message, reason).string)

    @bot.message_handler(commands=['warn'])
    def give_warn(message: Message):
        arguments = message.text.split(" ", 1)
        
        if len(arguments) == 1:
            reason = ""
        else:
            reason = arguments[1]

        if message.reply_to_message is None: 
            bot.reply_to(message, "Эта команда должна быть использована в ответ на сообщение пользователя, которого вы хотите предупредить.")
            return
        
        result = warn(bot, message.reply_to_message, reason)
        
        if isinstance(result, tuple):
            for msg in result:
                bot.reply_to(message, msg.string)
        else:
            bot.reply_to(message, result.string)



    @bot.message_handler(text_contains=["http://", "https://"])
    def moderation(message: Message):
        result = warn(bot, message, "Реклама")

        if result == UNABLE_TO_WARN_MESSAGE:
            return

        if isinstance(result, tuple):
            for msg in result:
                bot.reply_to(message, msg.string)
        else:
            bot.reply_to(message, result.string)


    @bot.message_handler(content_types=['new_chat_members'])
    def new_user(message: Message):
        bot.send_message(message.chat.id, f'Новый пользователь: @{message.from_user.username}!')
        bot.approve_chat_join_request(message.chat.id, message.from_user.id)

    bot.infinity_polling(none_stop=True, logger_level=logging.DEBUG)


if __name__ == "__main__":
    main()
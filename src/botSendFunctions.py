# This file contains functions for interacting with the Telegram API using the library
import telegram

def sendText(bot, chat_id, messageText, replyingMessageID=0, keyboardLayout=[], killkeyboard=True):
    bot.sendChatAction(chat_id=chat_id, action='typing')
    try:
        print("Sending " + messageText + " to " + str(chat_id))
    except Exception as e:
        print(str(e))

    if replyingMessageID != 0:
        bot.sendMessage(chat_id=chat_id, text=messageText, reply_to_message_id=replyingMessageID, reply_markup=telegram.ReplyKeyboardHide(hide_keyboard=killkeyboard))
    elif keyboardLayout != []:
        print("Sending custom keyboard")
        bot.sendMessage(chat_id=chat_id, text=messageText, reply_markup=telegram.ReplyKeyboardMarkup(keyboard=keyboardLayout, one_time_keyboard=True, resize_keyboard=True))
    else:
        bot.sendMessage(chat_id=chat_id, text=messageText, reply_markup=telegram.ReplyKeyboardHide(hide_keyboard=killkeyboard))

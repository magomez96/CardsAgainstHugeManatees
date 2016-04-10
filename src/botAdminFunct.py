# This file contains the functions for adding custom cards
from . import botSendFunctions

def customBlackCard(bot, currentMessage, chat_id):
    if len(currentMessage.text) > len("/addblackcard "):
        try: # Try to read in the white cards
            with open("chatStorage/blackCards.csv", "a") as csvfile:
                csvfile.write("\"" + currentMessage.text[14:] + "\"")
                csvfile.close()
            botSendFunctions.sendText(bot, chat_id, "Successfully added a custom black card.")
        except Exception:
            print("Couldn't open black card CSV files.")
            return
    else:
        botSendFunctions.sendText(bot, chat_id, "Please use the format, to insert a black use 5 underscores: /addblackcard card text here")


def customWhiteCard(bot, currentMessage, chat_id):
    if len(currentMessage.text) > len("/addwhitecard "):
        try: # Try to read in the white cards
            with open("chatStorage/whiteCards.csv", "a") as csvfile:
                csvfile.write("\"" + currentMessage.text[14:] + "\"")
                csvfile.close()
            botSendFunctions.sendText(bot, chat_id, "Successfully added a custom white card.")
        except Exception:
            print("Couldn't open white card CSV files.")
            return
    else:
        botSendFunctions.sendText(bot, chat_id, "Please use the format: /addwhitecard card text here")

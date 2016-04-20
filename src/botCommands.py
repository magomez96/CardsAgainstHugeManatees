# In this file handle any message that begins with / and either call the
# correct game functions or send error messages
import traceback
from . import botSendFunctions
from . import botGameEngine as game
from . import botAdminFunct as admin
from pydblite import Base

chatInstances = {}

def process(bot, chat_id, parsedCommand, messageText, currentMessage, update, instanceAge):
    def sendText(givenText, replyingMessageID=0, keyboardLayout=[]): # A simple wrapper for botSendFunctions.sendText()
        botSendFunctions.sendText(bot, chat_id, givenText, replyingMessageID, keyboardLayout)

    gameRecords = Base("chatStorage/records.pdl") # The following two lines create a DB to map gameID's to group chat ID's and player ID's
    gameRecords.create("gameID", "groupChatID", "memberUsernames", "memberUserIDs", "memberChatIDs", "memberPoints", "creator", "creatorChatID", "playerLimit", "started", mode="open")
    gameRecords.create_index("gameID") # Create a index to make selections by gameID
    gameRecords.create_index("groupChatID") # Create a index to make selections by groupChatID
    gameRecords.commit() # Save changes to disk

    try:
        try:
            chatInstances[chat_id]['checking'] = True
        except Exception:
            chatInstances[chat_id] = {'checking': True}
        print("Processing command " + messageText)
        if parsedCommand == "/help" or parsedCommand == "/start": # The default command Telegram sends to a bot is /start
            s = "This is the Cards Against Huge Manatees Bot\n"
            s += "To create a game type /newgame in a group chat or /newgame number to limit the number of players\n"
            s += "To join a game type /join [gameID] in a private chat with the bot\n"
            s += "To start the game after everyone has joined type /startgame in the group chat.\n"
            s += "A new black card will appear in the group chat and your white cards will appear\n"
            s += "in your private chat. The judge will choose the winner of each round.\n"
            s += "To end the game type /quit in the group chat\n"
            s += "To add a custom black card type /addblackcard the card text here To insert a blank use 5 underscores\n"
            s += "To add a custom white card type /addwhitecard the card text here"

            sendText(s)
        elif parsedCommand == "/newgame":
            ident = game.generate() # Generate a game ID
            if not len(currentMessage.text) > 9:
                gameRecords.insert(ident, str(chat_id), "", "", "", "", str(currentMessage.from_user.id), "", -1, 0) # Make a new database record skeleton
            else:
                try:
                    gameRecords.insert(ident, str(chat_id), "", "", "", "", str(currentMessage.from_user.id), "", abs(int(currentMessage.text.split()[1])), 0) # Make a new database record skeleton
                except Exception:
                    gameRecords.insert(ident, str(chat_id), "", "", "", "", str(currentMessage.from_user.id), "", -1, 0) # Make a new database record skeleton
            gameRecords.commit()
            sendText("The game ID is " + ident + " Please type /join " + ident + " in a private chat with the bot.") # Send the ID to the group chat

        elif parsedCommand == "/join":
            game.joinGame(bot, currentMessage, chat_id)
        elif parsedCommand == "/startgame":
            try:
                rec = gameRecords._groupChatID[str(chat_id)]
                rec = rec[-1]
                if not rec['started']:
                    game.initGameEnv(rec['gameID'])
                    game.playGame(bot, rec['gameID'])
                    gameRecords.update(rec, started=1)
                    gameRecords.commit()
                else:
                    sendText("Game already started.")
            except Exception:
                traceback.format_exc()
                sendText("Error. No game record for this chat found.")
        elif parsedCommand == "/ans":
            game.getAnswers(bot, currentMessage, chat_id)
        elif parsedCommand == "/win":
            game.winner(bot, currentMessage, chat_id)
        elif parsedCommand == "/quit":
            game.endGame(bot, currentMessage, chat_id)
        elif parsedCommand == "/addblackcard":
            admin.customBlackCard(bot, currentMessage, chat_id)
        elif parsedCommand == "/addwhitecard":
            admin.customWhiteCard(bot, currentMessage, chat_id)
        elif parsedCommand == "/pass":
            game.passPlayer(bot, currentMessage, chat_id)
        # elif parsedCommand == "/leave":
        #     game.leaveGame(bot, currentMessage, chat_id)
        elif parsedCommand[0] == "/": # Error handling
            sendText("Not a valid command")

    except Exception:
        print(traceback.format_exc())

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
    gameRecords.create("gameID", "groupChatID", "memberUsernames", "memberUserIDs", "memberChatIDs", "memberPoints", "creator", "creatorChatID", "started", mode="open")
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
            s += "To create a game type /newgame in a group chat\n"
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
            gameRecords.insert(ident, str(chat_id), "", "", "", "", currentMessage.from_user.id, "", 0) # Make a new database record skeleton
            gameRecords.commit()
            sendText("The game ID is " + ident + " Please type /join " + ident + " in a private chat with the bot.") # Send the ID to the group chat
        elif parsedCommand == "/join":
            rec = gameRecords._gameID[currentMessage.text.upper().split()[1]] # Get the DB record by GameID
            if not rec:
                sendText("Game ID not found.")
                return
            rec = rec[-1]
            if rec['started']: # If the game has already started they can't join.
                sendText("The game has already started. Sorry.")
                return
            if rec['groupChatID'] != str(chat_id):
                memberChats = rec['memberChatIDs']
                memberIDs = rec['memberUserIDs']
                memberNames = rec['memberUsernames']
                points = rec['memberPoints']
                if str(chat_id) not in memberChats:
                    if str(currentMessage.from_user.id) == str(rec['creator']):
                        gameRecords.update(rec, creatorChatID=chat_id)
                        gameRecords.commit()
                        sendText("You are the judge of game " + str(rec['gameID']))
                        return
                    memberChats += str(chat_id) + " " # String to list and back for the database.
                    memberIDs += str(currentMessage.from_user.id) + " "
                    memberNames += str(currentMessage.from_user.first_name) + " "
                    points += "0 "
                    gameRecords.update(rec, memberUsernames=memberNames, memberUserIDs=memberIDs, memberChatIDs=memberChats, memberPoints=points) # On every join update the database record
                    gameRecords.commit()
                    sendText("You have successfully joined the game " + str(rec['gameID']))
                else:
                    sendText("You have already joined the game.")
            else:
                sendText("Please type this command in a private chat with the bot.")
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
        elif parsedCommand[0] == "/": # Error handling
            sendText("Not a valid command")

    except Exception:
        print(traceback.format_exc())

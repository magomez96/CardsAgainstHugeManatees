import random
import string
import csv
from . import botSendFunctions
from . import globalVars
from random import shuffle
from pydblite import Base

def generate(): # Return a random 5 char string to act as the game ID
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))

def initGameEnv(gameID): # Initialize some globals and read in the cards from CSV
    try: # Try to read in the white cards
        globalVars.whiteCards = dict()
        with open("chatStorage/whiteCards.csv", "r") as csvfile:
            csvRead = csv.DictReader(csvfile)
            globalVars.whiteCards[gameID] = list(csvRead)
            shuffle(globalVars.whiteCards[gameID])
    except Exception:
        print("Couldn't open white card CSV files.")
        return
    try: # Try to read in the black cards
        globalVars.blackCards = dict()
        with open("chatStorage/blackCards.csv", "r") as csvfile:
            csvRead = csv.DictReader(csvfile)
            globalVars.blackCards[gameID] = list(csvRead)
            shuffle(globalVars.blackCards[gameID])
    except Exception:
        print("Couldn't open black card CSV files.")
        return

def playGame(bot, gameID): # Called by /startgame
    gameRecords = Base("chatStorage/records.pdl")
    gameRecords.open()
    rec = gameRecords._gameID[gameID]
    if not rec: # Error check
        return
    rec = rec[-1]
    globalVars.resp = dict()
    globalVars.resp[gameID] = dict()
    globalVars.currBlackCard = dict()

    def dealCards(): # Add random cards for every player
        players = rec['memberChatIDs'].split()
        globalVars.playerCards = dict()
        for player in players:
            l = [[] for _ in range(5)]
            globalVars.playerCards[player] = list()
            for i in range(5):
                card = globalVars.whiteCards[rec['gameID']].pop()['Value']
                l[i].append(str("/ans " + rec['gameID'] + " " + card))
            globalVars.playerCards[player] = l
            botSendFunctions.sendText(bot, player, "Here are your cards", 0, l)

    dealCards()
    globalVars.currBlackCard[gameID] = str(globalVars.blackCards[gameID].pop()['Value'])
    botSendFunctions.sendText(bot, rec['groupChatID'], globalVars.currBlackCard[gameID], 0, []) # Send a random black card to the group

def getAnswers(bot, currentMessage, chat_id): # Process the players responses here
    gameRecords = Base("chatStorage/records.pdl")
    gameRecords.open()
    rec = gameRecords._gameID[currentMessage.text[5:10]]
    if not rec:
        botSendFunctions.sendText(bot, chat_id, "Invalid command format")
        return
    rec = rec[-1]
    answer = currentMessage.text[11:]
    if currentMessage.text in [j for i in globalVars.playerCards[str(currentMessage.from_user.id)] for j in i] and not str(currentMessage.from_user.id) in globalVars.resp[rec['gameID']]:
        globalVars.resp[rec['gameID']][str(currentMessage.from_user.id)] = currentMessage.text[11:]
        emptyList = [] # List magic due to the way custom keyboards must be sent [[], [], []]
        try:
            emptyList.append("/ans " + str(rec['gameID']) + " " + globalVars.whiteCards[rec['gameID']].pop()['Value'])
        except IndexError:
            botSendFunctions.sendText(bot, rec['groupChatID'], "Sorry. Out of cards, game over.")
            endGame(bot, currentMessage, chat_id)
            return
        for i in range(len(globalVars.playerCards[str(chat_id)])):
            if currentMessage.text in globalVars.playerCards[str(chat_id)][i]:
                globalVars.playerCards[str(chat_id)].pop(i)
                break
        globalVars.playerCards[str(chat_id)].append(emptyList)
        newStr = globalVars.currBlackCard[rec['gameID']].replace("_____", str(answer)) # Send all the responses to the group chat
        if newStr == globalVars.currBlackCard[rec['gameID']]: # Handling for cards with no 'blank'
            botSendFunctions.sendText(bot, rec['groupChatID'], str(answer))
        else:
            botSendFunctions.sendText(bot, rec['groupChatID'], newStr)
        botSendFunctions.sendText(bot, chat_id, "Answer recieved.")
        if set(globalVars.resp[rec['gameID']].keys()) == set(rec['memberUserIDs'].split()): # If everyone has responded call judge
            judge(bot, currentMessage.text[5:10], chat_id)
    else:
        botSendFunctions.sendText(bot, chat_id, "Invaild card sent.", keyboardLayout=globalVars.playerCards[str(chat_id)])

def judge(bot, gameID, chat_id): # Send all the responses to the judge
    gameRecords = Base("chatStorage/records.pdl")
    gameRecords.open()
    rec = gameRecords._gameID[gameID]
    if not rec:
        botSendFunctions.sendText(bot, chat_id, "Invalid command format")
        return
    rec = rec[-1]
    l = [[] for _ in range(len(globalVars.resp[rec['gameID']]))]
    i = 0
    for ans in globalVars.resp[rec['gameID']].values():
        l[i].append("/win " + gameID + " " + str(ans))
        i += 1
    botSendFunctions.sendText(bot, rec['creatorChatID'], "Here are the responses", keyboardLayout=l)

def winner(bot, currentMessage, chat_id): # Decide who wins here. Only the judge is able to use this
    gameRecords = Base("chatStorage/records.pdl")
    gameRecords.open()
    rec = gameRecords._gameID[currentMessage.text[5:10]]
    if not rec:
        botSendFunctions.sendText(bot, chat_id, "Invalid command format")
        return
    rec = rec[-1]
    if currentMessage.from_user.id == rec['creator']:
        revD = {value: key for key, value in globalVars.resp[rec['gameID']].items()}
        winningResp = currentMessage.text[11:]
        if winningResp in revD.keys():
            winningPerson = revD[winningResp]
            pointsList = rec['memberPoints'].split() # List stuff for the database
            memberList = rec['memberUserIDs'].split()
            nameList = rec['memberUsernames'].split()
            pointsList[memberList.index(winningPerson)] = int(pointsList[memberList.index(winningPerson)]) + 1
            gameRecords.update(rec, memberPoints=" ".join([str(i) for i in pointsList])) # Points backend for Assign 3
            gameRecords.commit()
            botSendFunctions.sendText(bot, rec['groupChatID'], "The winner was " + nameList[memberList.index(winningPerson)] + " with " + winningResp + " They now have " + str(pointsList[memberList.index(winningPerson)]) + " point(s).") # Send who won to the group chat
            try:
                globalVars.currBlackCard[currentMessage.text[5:10]] = str(globalVars.blackCards[rec['gameID']].pop()['Value']) # Get the next black card
            except IndexError: # If there are no more cards end the game
                botSendFunctions.sendText(bot, rec['groupChatID'], "Sorry, out of cards. Thanks for playing")
                endGame(bot, currentMessage, chat_id)
                return
            botSendFunctions.sendText(bot, rec['groupChatID'], globalVars.currBlackCard[currentMessage.text[5:10]]) # Send the next black card
            for player in rec['memberChatIDs'].split(): # Send all the players a new card to replace the one they used
                if player in globalVars.resp[rec['gameID']]:
                    del globalVars.resp[rec['gameID']][player]
                    botSendFunctions.sendText(bot, player, "Here are your new cards", 0, globalVars.playerCards[player])
        else:
            botSendFunctions.sendText(bot, chat_id, "Invalid answer")
    else:
        botSendFunctions.sendText(bot, chat_id, "You are not the judge")

def passPlayer(bot, currentMessage, chat_id):
    gameRecords = Base("chatStorage/records.pdl")
    gameRecords.open()
    rec = gameRecords._groupChatID[str(chat_id)] # select all the records with chat_id (only 1)
    if not rec:
        botSendFunctions.sendText(bot, chat_id, "Invalid command format")
        return
    rec = rec[-1] # Strip the last record from the list
    if str(currentMessage.from_user.id) == str(rec['creator']) and len(globalVars.resp[rec['gameID']]) > 0:
        judge(bot, rec['gameID'], chat_id)
    elif len(globalVars.resp[rec['gameID']]) == 0:
        try:
            globalVars.currBlackCard[currentMessage.text[5:10]] = str(globalVars.blackCards[rec['gameID']].pop()['Value']) # Get the next black card
        except IndexError: # If there are no more cards end the game
            botSendFunctions.sendText(bot, rec['groupChatID'], "Sorry, out of cards. Thanks for playing")
            endGame(bot, currentMessage, chat_id)
            return
        botSendFunctions.sendText(bot, rec['groupChatID'], globalVars.currBlackCard[currentMessage.text[5:10]]) # Send the next black card
    else:
        botSendFunctions.sendText(bot, chat_id, "Sorry. Only the judge can pass.")

def leaveGame(bot, currentMessage, chat_id):
    gameRecords = Base("chatStorage/records.pdl")
    gameRecords.open()
    rec = gameRecords._groupChatID[str(chat_id)] # select all the records with chat_id (only 1)
    if not rec:
        botSendFunctions.sendText(bot, chat_id, "Invalid command format")
        return
    rec = rec[-1] # Strip the last record from the list
    memberChats = rec['memberChatIDs'].split()
    memberIDs = rec['memberUserIDs'].split()
    memberNames = rec['memberUsernames'].split()
    points = rec['memberPoints'].split()
    playerIndex = memberIDs.index(str(currentMessage.from_user.id))
    memberIDs.pop(playerIndex)
    try:
        playerChat = str(memberChats.pop(playerIndex))
        del globalVars.playerCards[playerChat]
        del globalVars.resp[rec['gameID']][playerChat]
    except Exception:
        pass
    memberNames.pop(playerIndex)
    points.pop(playerIndex)
    gameRecords.update(rec, memberUsernames=str(memberNames), memberUserIDs=str(memberIDs), memberChatIDs=str(memberChats), memberPoints=str(points))
    gameRecords.commit()

def endGame(bot, currentMessage, chat_id): # /quit behavior ends the game for everyone
    gameRecords = Base("chatStorage/records.pdl")
    gameRecords.open()
    rec = gameRecords._groupChatID[str(chat_id)] # select all the records with chat_id (only 1)
    if not rec:
        botSendFunctions.sendText(bot, chat_id, "Invalid command format")
        return
    rec = rec[-1] # Strip the last record from the list

    pointsBoard = "Here are the scores\n" # Send the final scores to the group
    for name, points in zip(rec['memberUsernames'].split(), rec['memberPoints'].split()):
        pointsBoard += str(name) + ": " + str(points) + " point(s)\n"
    botSendFunctions.sendText(bot, chat_id, pointsBoard)

    for player in rec['memberChatIDs'].split(): # Clean out the playerCards global
        try:
            del globalVars.playerCards[player]
        except Exception: # If a player isn't there ignore it
            pass
    try:
        del globalVars.resp[rec['gameID']] # Delete the game's responses key
        del globalVars.currBlackCard[rec['gameID']] # Delete the game's current black card key
        del globalVars.whiteCards[rec['gameID']]
    except Exception:
        pass
    gameRecords.delete(rec) # Remove the database record
    gameRecords.commit() # Save the changes

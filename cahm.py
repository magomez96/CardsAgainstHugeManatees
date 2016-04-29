# Cards Against Huge Manatees

import telegram
import csv
import traceback
import datetime
import re
import time
import src.botCommands as Commands
from src import globalVars

APIKEY = ""
with open('apikey.csv', 'r') as csvfile: # Read in the API key from the .csv file
    reader = csv.DictReader(csvfile)
    APIKEY = list(reader)[0]['key']

cahm = telegram.Bot(token=APIKEY) # Make the bot object

updates = list() # A list for updates from the teleram chat
currMess = list() # A list to hold the current message we're looking at

globalVars.init() # Bring in the global variables

print("Cards Against Huge Manatees Bot 3.0")
print("Team Synergy")

newestOffset = 0
networkFailure = False
while not networkFailure: # Get the initial batch of chat messages
    try:
        updates = cahm.getUpdates(offset=newestOffset, timeout=3, network_delay=5)
        for update in updates:
            newestOffset = update.update_id
        networkFailure = True
    except Exception:
        print(traceback.format_exc())
        print("...", end=' ')
print("Connected to Telegram.")

startTime = datetime.datetime.now() # Record the time the bot started

instanceAge = 0

blacklist = [] # Blacklist to ban abusive chat groups

running = True
while running: # Continue to get updates from the different chat groups forever
    networkFailure = False
    while not networkFailure:
        try:
            updates = cahm.getUpdates(offset=newestOffset + 1)
            for update in updates:
                newestOffset = update.update_id
            networkFailure = True
        except Exception:
            print("...err...")

    if instanceAge % 10 == 0: # Print 1 X every ten ticks
        print("")
    else:
        print("X", end=" ")

    for update in updates: # Go through each message and execute commands
        currentMessage = update.message
        try:
            chat_id = currentMessage.chat.id
            if chat_id not in blacklist:
                parsedCommand = re.split(r'[@\s:,\'*]', currentMessage.text.lower())[0]
                Commands.process(cahm, chat_id, parsedCommand, currentMessage.text, currentMessage, update, datetime.datetime.now() - startTime) # Handoff to the game logic if the message begins with /
                time.sleep(1) # Keep the bot from flooding the network interface with requests
        except Exception: # If anything goes wrong print to the console but keep going
            print(traceback.format_exc())
    time.sleep(2) # Keep the bot from flooding the network interface with requests
    instanceAge += 1

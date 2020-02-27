# ---------------------------------------
#   Import Libraries
# ---------------------------------------
import clr
import re
import json
import codecs
import os
import time
import random

clr.AddReference("IronPython.Modules.dll")

# ---------------------------------------
#   [Required]  Script Information
# ---------------------------------------
ScriptName = "Did U Know"
Website = "https://www.twitch.tv/frittenfettsenpai"
Description = "Reeyyyyyye."
Creator = "frittenfettsenpai"
Version = "0.1.0"


# ---------------------------------------
#   [Required] Intialize Data (Only called on Load)
# ---------------------------------------
def Init():
    global settings, questions, activeQuestion, activeFor, activeUser, creatorActiveFor, solution
    settingsfile = os.path.join(os.path.dirname(__file__), "settings.json")
    datafile = os.path.join(os.path.dirname(__file__), "questions.json")

    try:
        with codecs.open(datafile, encoding="utf-8-sig", mode="r") as f:
            questions = json.load(f, encoding="utf-8")
            f.close()
    except:
        questions = {}

    try:
        with codecs.open(settingsfile, encoding="utf-8-sig", mode="r") as f:
            settings = json.load(f, encoding="utf-8")
            f.close()
    except:
        settings = {
            "enableDidYouKnow": True,
            "gameCommand": "!diduknow",
            "startGameCosts": 100,
            "winnerPrice": 50,
            "winnerFullPrice": 100,
            "languageGotCurrency": "{0} hat nach dem Wipe {1} {2} bekommen.",
            "userCooldownInSeconds": 100,
            "activeFor": 120,
            "creatorActiveFor": 120,
            "whisperCommand": "!know",
            "languageStartWhisper": "{0}. Bitte beantworte die Frage mit der Skala '{1} 0-100'. 0={2} || 100={3}",
            "languageStartChat": "Von einer Skala zwischen 0 und 100: {0} 0={1} || 100={2}"
        }

    activeQuestion = None
    activeUser = None
    solution = None
    activeFor = 0
    creatorActiveFor = 0
    return


# ---------------------------------------
#   [Required] Execute Data / Process Messages
# ---------------------------------------
def Execute(data):
    global settings, questions, activeQuestion, activeFor, activeUser, creatorActiveFor, solution

    if data.IsChatMessage():
        user = data.User
        command = data.GetParam(0).lower()
        if settings["enableDidYouKnow"] and command == settings["gameCommand"] and activeQuestion is None:
            if Parent.IsOnCooldown("DidUKnow", settings["gameCommand"]) and Parent.HasPermission(user, "Caster", "") is False:
                cooldown = Parent.GetCooldownDuration("Gachapon", settings["gachaponcommand"])
                Parent.SendTwitchMessage(settings["languageCooldown"].format(cooldown, settings["gameCommand"]))
                return
            if Parent.GetPoints(user) < settings['startGameCosts']:
                Parent.SendTwitchMessage(settings["languageNoMoney"].format(user, settings['startGameCosts'], Parent.GetCurrencyName()))
                return
            Parent.AddCooldown(ScriptName, settings['gameCommand'], settings['userCooldown'])

            if int(settings['startGameCosts']) > 0:
                Parent.RemovePoints(user, int(settings['startGameCosts']))

            random.seed(time.clock())
            activeQuestion = random.choice(questions)
            activeUser = user
            creatorActiveFor=settings['creatorActiveFor']
            Parent.SendStreamWhisper(activeUser, settings["languageStartWhisper"].format(activeQuestion["question"], settings["whisperCommand"], activeQuestion["left"], activeQuestion["right"]))
        elif activeQuestion is not None:
            # Handle chat
            return

    if data.IsWhisper() and activeUser is not None:
        command = data.GetParam(0).lower()
        if activeUser == data.User and command == settings["whisperCommand"] and int(data.GetParam(1)) >= 0 and int(data.GetParam(1)) <= 100:
            activeFor = settings['activeFor']
            solution = int(data.GetParam(1))
            Parent.SendTwitchMessage(settings["languageStartChat"].format(activeQuestion["question"].format(activeUser), activeQuestion['left'], activeQuestion['right']))
            return



    return


# ---------------------------------------
#	[Required] Tick Function
# ---------------------------------------
def Tick():
    global settings, activeQuestion, activeFor, activeUser, creatorActiveFor, solution
    if activeUser is None:
        return

    time.sleep(1)
    if activeFor > 0:
        activeFor = activeFor - 1
    elif creatorActiveFor > 0:
        creatorActiveFor = creatorActiveFor - 1
    else:
        # Game end
        activeQuestion = None
        activeUser = None
        solution = None
        activeFor = 0
    return
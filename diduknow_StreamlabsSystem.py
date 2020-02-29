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
Version = "0.5.0"


# ---------------------------------------
#   [Required] Intialize Data (Only called on Load)
# ---------------------------------------
def Init():
    global settings, questions, activeQuestion, activeFor, activeUser, creatorActiveFor, solution, playerChoices
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
            "userCooldownInSeconds": 1000,
            "activeFor": 120,
            "creatorActiveFor": 120,
            "command": "!know",
            "languageStartWhisper": "@{0}. Bitte beantworte die Frage mit der Skala (Nur die Zahl) '0-100': {1} || 0={2} || 100={3}",
            "languageStartChat": "Von einer Skala zwischen 0 und 100:  100={2} || ({3} Zahl)",
            "languageGameEndNoOne": "Niemand hat mitgemacht, also gewinnt auch ni{0} 0={1} ||emand!",
            "languageGameEndNearest": "Die Loesung von @{0} Frage ist {1}. Am nachsten dran mit {2} waren folgende Spieler: {3}.",
            "languageGameEndSame": "Die Loesung von @{0} Frage ist {1}. Das wussten natuerlich direkt folgende Spieler: {2}",
            "languageGameEndPrice": "Die Gewinner bekommen dafuer {0} {1}",
            "languageCooldown": "@{0} you have to wait {1} seconds to use {2} again!",
            "languageNoMoney": "@{0} you need atleast {1} {2}!",
        }

    activeQuestion = None
    activeUser = None
    solution = None
    activeFor = 0
    creatorActiveFor = 0
    playerChoices = {}
    return


# ---------------------------------------
#   [Required] Execute Data / Process Messages
# ---------------------------------------
def Execute(data):
    global settings, questions, activeQuestion, activeFor, activeUser, creatorActiveFor, solution, playerChoices

    if data.IsWhisper() and activeUser is not None:
        tmpSolution = int(data.GetParam(0))
        if activeUser == data.User and tmpSolution >= 0 and tmpSolution <= 100:
            activeFor = settings['activeFor']
            solution = tmpSolution
            Parent.SendTwitchMessage(settings["languageStartChat"].format(activeQuestion["questionChat"].format(activeUser), activeQuestion['left'], activeQuestion['right'], settings["command"]))
            return

    if data.IsChatMessage():
        user = data.User
        command = data.GetParam(0).lower()
        if settings["enableDidYouKnow"] and command == settings["gameCommand"] and activeQuestion is None:
            if Parent.IsOnCooldown(ScriptName, settings["gameCommand"]) and Parent.HasPermission(user, "Caster", "") is False:
                cooldown = Parent.GetCooldownDuration(ScriptName, settings["userCooldownInSeconds"])
                Parent.SendTwitchMessage(settings["languageCooldown"].format(user, cooldown, settings["gameCommand"]))
                return
            if Parent.GetPoints(user) < settings['startGameCosts']:
                Parent.SendTwitchMessage(settings["languageNoMoney"].format(user, settings['startGameCosts'], Parent.GetCurrencyName()))
                return
            Parent.AddCooldown(ScriptName, settings['gameCommand'], settings['userCooldownInSeconds'])

            if int(settings['startGameCosts']) > 0:
                Parent.RemovePoints(user, int(settings['startGameCosts']))

            random.seed(time.clock())
            activeQuestion = random.choice(questions)
            activeUser = user
            creatorActiveFor = settings['creatorActiveFor']
            Parent.SendStreamWhisper(activeUser, settings["languageStartWhisper"].format(activeUser, activeQuestion["question"], activeQuestion["left"], activeQuestion["right"]))
        elif activeQuestion is not None and command == settings["command"] and user != activeUser:
            # Handle chat
            if user not in playerChoices.keys():
                choice = int(data.GetParam(1))
                if choice >= solution:
                    diff = choice - solution
                else:
                    diff = solution - choice
                playerChoices[user] = {"choice": choice, "diff": diff}
            return
    return


# ---------------------------------------
#	[Required] Tick Function
# ---------------------------------------
def Tick():
    global settings, activeQuestion, activeFor, activeUser, creatorActiveFor, solution, playerChoices
    if activeUser is None:
        return

    time.sleep(1)
    if activeFor > 0:
        activeFor = activeFor - 1
    elif creatorActiveFor > 0:
        creatorActiveFor = creatorActiveFor - 1
    else:
        # Game end
        nearestDiff = 100
        nearestSolution = None
        nearest
        for userName, userData in playerChoices.items():
            if userData["diff"] < nearestDiff:
                nearestDiff = userData["diff"]

        playerWon = []
        for userName, userData in playerChoices.items():
            if userData["diff"] == nearestDiff:
                playerWon.append(userName)
                nearestSolution = userData["choice"]

        if len(playerWon) == 0:
            Parent.SendTwitchMessage(settings["languageGameEndNoOne"])
        else:
            if solution == nearestSolution:
                message = settings["languageGameEndSame"].format(activeUser, str(solution), ','.join(playerWon))
                price = settings["winnerFullPrice"]
            else:
                message = settings["languageGameEndNearest"].format(activeUser, str(solution), nearestSolution, ','.join(playerWon))
                price = settings["winnerPrice"]

            if price > 0:
                for player in playerWon:
                    Parent.AddPoints(player, int(price))
                message = message + settings["languageGameEndPrice"].format(str(price), Parent.GetCurrencyName())

            Parent.SendTwitchMessage(message)
        activeQuestion = None
        activeUser = None
        solution = None
        activeFor = 0
        creatorActiveFor = 0
        playerChoices = {}
    return
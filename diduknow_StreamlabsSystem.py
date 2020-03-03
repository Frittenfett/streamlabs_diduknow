# -*- coding: utf-8 -*-
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
Description = "Did U Know - Minigame"
Creator = "frittenfettsenpai"
Version = "1.1.0"


# ---------------------------------------
#   [Required] Intialize Data (Only called on Load)
# ---------------------------------------
def Init():
    global settings, questions, activeQuestion, activeFor, activeUser, creatorActiveFor, solution, playerChoices, stackCounter
    settingsfile = os.path.join(os.path.dirname(__file__), "settings.json")

    try:
        with codecs.open(settingsfile, encoding="utf-8-sig", mode="r") as f:
            settings = json.load(f, encoding="utf-8")
            f.close()
    except:
        settings = {
            "enableDidYouKnow": True,
            "language": "de",
            "questionRandomizerType": "random",
            "gameCommand": "!guessinggame",
            "startGameCosts": 100,
            "winnerPrice": 50,
            "winnerFullPrice": 100,
            "userCooldownInSeconds": 1000,
            "activeFor": 90,
            "creatorActiveFor": 120,
            "command": "!guess",
            "languageStartGame": "Wie gut kennt ihr @{0} wirklich? @{0} hat eine private Flüster-Nachricht bekommen und muss innerhalb von {1} Sekunden dort antworten. Und schon gehts dann los.!",
            "languageStartWhisper": "@{0}. Bitte beantworte die Frage auf einer Skala (Nur die Zahl) von '0-100': {1} || 0={2} || 100={3}",
            "languageStartChat": "Auf einer Skala von 0 bis 100 ({3} Zahl): {0} 0={1} || 100={2} || Ihr habt {4} Sekunden Zeit!",
            "languageGameEndNoOne": "Niemand hat mitgemacht, also gewinnt auch niemand!",
            "languageGameEndNearest": "Die Lösung von @{0} Frage '{4}' ist {1}. Am nächsten dran mit {2} waren folgende Spieler: {3}",
            "languageGameEndSame": "Die Lösung von @{0} Frage '{3}' ist {1}. Das wussten natürlich direkt folgende Spieler: {2}",
            "languageGameEndPrice": "Die Gewinner bekommen dafür {0} {1}",
            "languageCooldown": "@{0} Du musst {1} Sekunden warten, bevor du {2} nutzen kannst!",
            "languageNoMoney": "@{0} du benötigst mindestens {1} {2}!",
            "languageAverage": "Der Durchschnitts-Wert der Teilnehmer war {0}",
            "languageToSlow": "@{0} war zu langsam. Ihr könnt wieder {1} benutzen.",
            "language30Seconds": "Nur noch 30 Sekunden... Stimmt jetzt ab mit '{0} Zahl'",
        }

    datafile = os.path.join(os.path.dirname(__file__), "questions_" + settings["language"] + ".json")
    try:
        with codecs.open(datafile, encoding="utf-8-sig", mode="r") as f:
            questions = json.load(f, encoding="utf-8")
            random.seed(time.clock())
            random.shuffle(questions)
            f.close()
    except:
        questions = {}

    stackCounter = 0
    ResetGame()
    return


# ---------------------------------------
#   [Required] Execute Data / Process Messages
# ---------------------------------------
def Execute(data):
    global settings, questions, activeQuestion, activeFor, activeUser, creatorActiveFor, solution, playerChoices, stackCounter

    if data.IsWhisper() and activeUser is not None:
        tmpSolution = int(data.GetParam(0))
        if activeUser == data.User and creatorActiveFor > 0 and tmpSolution >= 0 and tmpSolution <= 100:
            activeFor = settings['activeFor']
            solution = tmpSolution
            creatorActiveFor = 0
            Parent.SendTwitchMessage(settings["languageStartChat"].format(activeQuestion["questionChat"].format(activeUser), activeQuestion['left'], activeQuestion['right'], settings["command"], str(activeFor)))
            return

    if data.IsChatMessage():
        user = data.User
        command = data.GetParam(0).lower()
        if settings["enableDidYouKnow"] and command == settings["gameCommand"] and activeQuestion is None:
            if Parent.IsOnCooldown(ScriptName, settings["gameCommand"]) and Parent.HasPermission(user, "Caster", "") is False:
                cooldown = Parent.GetCooldownDuration(ScriptName, settings["gameCommand"])
                Parent.SendTwitchMessage(settings["languageCooldown"].format(user, cooldown, settings["gameCommand"]))
                return
            if Parent.GetPoints(user) < settings['startGameCosts']:
                Parent.SendTwitchMessage(settings["languageNoMoney"].format(user, settings['startGameCosts'], Parent.GetCurrencyName()))
                return
            Parent.AddCooldown(ScriptName, settings['gameCommand'], settings['userCooldownInSeconds'])

            if int(settings['startGameCosts']) > 0:
                Parent.RemovePoints(user, int(settings['startGameCosts']))

            if settings["questionRandomizerType"] == "random":
                random.seed(time.clock())
                activeQuestion = random.choice(questions)
            else:
                activeQuestion = questions[stackCounter]
                stackCounter = stackCounter + 1
                if stackCounter >= len(questions):
                    stackCounter = 0
            activeUser = user
            creatorActiveFor = settings['creatorActiveFor']
            Parent.SendTwitchMessage(settings["languageStartGame"].format(user, str(creatorActiveFor)))
            Parent.SendStreamWhisper(activeUser, settings["languageStartWhisper"].format(activeUser, activeQuestion["question"], activeQuestion["left"], activeQuestion["right"]))
        elif activeQuestion is not None and activeFor > 0 and command == settings["command"] and user != activeUser:
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
        if activeFor == 30:
            Parent.SendTwitchMessage(settings["language30Seconds"].format(settings['command']))
    elif creatorActiveFor > 0:
        creatorActiveFor = creatorActiveFor - 1
        if creatorActiveFor == 0:
            Parent.SendTwitchMessage(settings["languageToSlow"].format(settings['activeUser'], settings['gameCommand']))
            ResetGame()
    else:
        # Game end
        nearestDiff = 100
        nearestSolution = None
        for userName, userData in playerChoices.items():
            if userData["diff"] < nearestDiff:
                nearestDiff = userData["diff"]

        playerWon = []
        summary = 0
        playerAmount = 0
        for userName, userData in playerChoices.items():
            summary = summary + int(userData["choice"])
            playerAmount = playerAmount + 1
            if userData["diff"] == nearestDiff:
                playerWon.append(userName)
                nearestSolution = userData["choice"]

        if len(playerWon) == 0:
            Parent.SendTwitchMessage(settings["languageGameEndNoOne"])
            ResetGame()
        else:
            if solution == nearestSolution:
                message = settings["languageGameEndSame"].format(activeUser, str(solution), ', '.join(playerWon), activeQuestion["question"])
                price = settings["winnerFullPrice"]
            else:
                message = settings["languageGameEndNearest"].format(activeUser, str(solution), nearestSolution, ', '.join(playerWon), activeQuestion["question"])
                price = settings["winnerPrice"]

            average = int(summary / playerAmount)
            message = message + ". " + settings["languageAverage"].format(str(average))

            if price > 0:
                for player in playerWon:
                    Parent.AddPoints(player, int(price))
                message = message + ". " + settings["languageGameEndPrice"].format(str(price), Parent.GetCurrencyName())

            Parent.SendTwitchMessage(message)
            ResetGame()
    return


def ResetGame():
    global settings, activeQuestion, activeFor, activeUser, creatorActiveFor, solution, playerChoices
    activeQuestion = None
    activeUser = None
    solution = None
    activeFor = 0
    creatorActiveFor = 0
    playerChoices = {}
    Parent.AddCooldown(ScriptName, settings['gameCommand'], 1)

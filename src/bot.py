#!/usr/bin/env python3

"""Connects the bot."""

import datetime
import getpass
import json
import os.path
import random
import re
import sys
import threading
import time

import cucco
import hclib

import utility
from commands import arithmetic
from commands import currency
from commands import jokes
from commands import dictionary
from commands import katex
from commands import password
from commands import paste
from commands import poetry
from commands import search


class HackChatBot:
    """Activates the bot and prints warnings recieved to the console.

    Use the <join> function to join channels.
    """

    def __init__(self):
        """Initializes values."""
        random.seed(datetime.datetime.now())
        self._config = json.loads(open("data/config.json").read())
        if (not self._config["name"] or not self._config["channels"]
            or not self._config["trigger"]):
            sys.exit("Make sure you have entered \"name\", \"channel\" and "
                     + "\"trigger\" in config.json located in the src folder.")
        self._charsPerLine = 88
        self._maxLines = 8
        self._maxChars = self._charsPerLine * self._maxLines
        self._commands = [
            "afk", "alias", "h", "help", "join", "joke", "katex", "leave",
            "math", "msg", "poem", "poet", "password", "search", "stats",
            "toss", "urban"
        ]
        if self._config["oxfordAppId"] and self._config["oxfordAppKey"]:
            self._commands += ["define", "translate"]
        if self._config["exchangeRateApiKey"]:
            self._commands.append("rate")
        self._oxford = dictionary.Oxford(self._config["oxfordAppId"],
                                         self._config["oxfordAppKey"])

    def _handle(self, hackChat, info):
        """Callback function for data sent from https://hack.chat.

        <hackChat> (callback parameter) is the connection object.
        <info> (callback parameter) is the data sent.
        """
        self._hackChat = hackChat
        self._type = info["type"]
        self._nick = info["nick"] if "nick" in info else None
        self._text = info["text"].strip() if "text" in info else None
        self._trip = info["trip"] if "trip" in info else None
        self._channel = info["channel"] if "channel" in info else None
        self._ip = info["ip"] if "ip" in info else None
        self._warning = info["warning"] if "warning" in info else None
        self._ips = info["IPs"] if "IPs" in info else None
        self._channels = info["channels"] if "channels" in info else None
        if self._type == "invite":
            self.join(self._channel)
        elif self._type == "message":
            if self._nick != self._config["name"]:
                self._check_afk()
            self._post()
            if self._trip:
                self._log_trip_code()
            space = re.search(r"\s", self._text)
            self._msg = self._text[space.end():].strip() if space else None
            call = self._text[:len(self._config["trigger"])]
            if call == self._config["trigger"]:
                check = space.start() if space else len(self._text)
                self._cmd = self._text[len(self._config["trigger"]):check]
                self._message()
        elif self._type == "online add":
            self._post()
        elif self._type == "online remove":
            afkUsers = json.loads(open("data/afk.json").read())
            if self._nick in afkUsers:
                afkUsers.pop(self._nick)
                with open("data/afk.json", "w") as f:
                    json.dump(afkUsers, f, indent = 4)
        elif self._type == "stats":
            self._stats()
        elif self._type == "warn":
            self._warn()

    def join(self, channel):
        """Joins <channel> (<str>)."""
        connector = hclib.HackChat(
            self._handle, self._config["name"], channel,
            self._config["password"], self._config["url"])

    def _check_afk(self):
        """Notifies AFK statuses."""
        afkUsers = json.loads(open("data/afk.json").read())
        if not self._hackChat.channel in afkUsers:
            return
        afkUsersChannel = afkUsers[self._hackChat.channel]
        cmd = "{}afk".format(self._config["trigger"])
        if self._nick in afkUsersChannel and not re.match(cmd, self._text):
            afkUsersChannel.pop(self._nick)
            with open("data/afk.json", "w") as f:
                json.dump(afkUsers, f, indent = 4)
        reply = ""
        for user in afkUsersChannel:
            person = " @{} ".format(user)
            if person in " {} ".format(self._text):
                reply += person.strip()
                if afkUsersChannel[user]:
                    reply += ": {}".format(afkUsersChannel[user])
                reply += "\n"
        if reply:
            self._hackChat.send("@{} AFK users:\n{}".format(self._nick, reply))

    def _log_trip_code(self):
        """Logs nicknames along with their trip codes."""
        verifiers = json.loads(open("data/trip_codes.json").read())
        if self._trip in verifiers and self._nick not in verifiers[self._trip]:
            verifiers[self._trip].append(self._nick)
        elif self._trip not in verifiers:
            verifiers[self._trip] = [self._nick]
        with open("data/trip_codes.json", "w") as f:
            json.dump(verifiers, f, indent = 4)

    def _post(self):
        """Sends messages saved for people."""
        messages = json.loads(open("data/messages.json").read())
        if self._nick in messages:
            reply = ""
            for msg in messages[self._nick]:
                reply += "@{}: {}\n".format(msg["sender"], msg["message"])
            messages.pop(self._nick)
            with open("data/messages.json", "w") as f:
                json.dump(messages, f, indent = 4)
            self._hackChat.send(
                "@{} you have messages:\n{}".format(self._nick, reply))

    def _stats(self):
        """Sends statistics."""
        self._hackChat.send("There are {} unique IPs in ".format(self._ips)
                            + "{} channels.".format(self._channels))

    def _warn(self):
        """Handles warnings."""
        msg = utility.date_format("warning", self._warning)
        print("\n{}".format(msg))

    def _message(self):
        """Redirects commands to their respective wrapper functions."""
        if self._cmd == "afk":
            self._afk()
        elif self._cmd == "alias":
            self._alias()
        elif self._cmd == "define" and "define" in self._commands:
            self._define()
        elif (self._cmd == "h" and not self._msg) or self._cmd == "help":
            self._help()
        elif self._cmd == "join":
            self._joiner()
        elif self._cmd == "joke":
            self._joke()
        elif self._cmd[:len("katex")] == "katex":
            self._katex_converter()
        elif self._cmd == "leave":
            self._leave()
        elif self._cmd == "math":
            self._math()
        elif self._cmd[:len("msg")] == "msg":
            self._messenger()
        elif self._cmd == "password":
            self._strengthen()
        elif self._cmd == "poem" or self._cmd == "poet":
            self._poem()
        elif self._cmd[:len("rate")] == "rate" and "rate" in self._commands:
            self._rate()
        elif self._cmd == "search":
            self._answer()
        elif self._cmd == "stats":
            self._get_stats()
        elif self._cmd == "toss":
            self._toss()
        elif (self._cmd[:len("translate")] == "translate"
              and "translate" in self._commands):
            self._translate()
        elif self._cmd == "urban":
            self._urban()

    def _alias(self):
        """Sends the requested trip codes' holdees."""
        if self._msg:
            verifiers = json.loads(open("data/trip_codes.json").read())
            if self._msg in verifiers:
                nicks = ", ".join(verifiers[self._msg])
                reply = ("@{} {} has the ".format(self._nick, self._msg)
                         + "aliases {}".format(nicks))
                nicks = utility.shorten(reply, self._maxChars, " ")
                self._hackChat.send(reply)
            else:
                self._hackChat.send(
                    "@{} no aliases were found".format(self._nick))
        else:
            self._hackChat.send(
                "@{} tells the trip codes' aliases (e.g., ".format(self._nick)
                + "{}alias dIhdzE)".format(self._config["trigger"]))

    def _afk(self):
        """Handles AFK statuses."""
        afkUsers = json.loads(open("data/afk.json").read())
        if self._hackChat.channel not in afkUsers:
            afkUsers[self._hackChat.channel] = {}
        afkUsers[self._hackChat.channel][self._nick] = self._msg
        with open("data/afk.json", "w") as f:
            json.dump(afkUsers, f, indent = 4)
        reply = "@{} is now AFK".format(self._nick)
        if self._msg:
            reply += ": {}".format(self._msg)
        self._hackChat.send(reply)

    def _answer(self):
        """Handles searches."""
        if self._msg:
            results = search.duckduckgo(self._msg, "hack.chat bot")
            reply = ""
            if len(results["URL"]) > 0:
                reply += "{} ".format(results["URL"])
            if len(results["Heading"]) > 0:
                reply += "{}: ".format(results["Heading"])
            if len(results["Answer"]) > 0:
                reply += results["Answer"]
            elif len(results["AbstractText"]) > 0:
                reply += results["AbstractText"]
            else:
                reply = ""
            tell = "@{} ".format(self._nick)
            reply = utility.shorten(reply, self._maxChars - len(tell), ".")
            if not reply:
                reply = "Sorry, I couldn't find anything."
            self._hackChat.send(tell + reply)
        else:
            self._hackChat.send("@{} instant answers ".format(self._nick)
                                + "(e.g., {}search ".format(config["trigger"])
                                + "pokemon ruby)")

    def _define(self):
        """Handles definitions."""
        if self._msg:
            data = self._oxford.define(self._msg)
            if data["type"] == "success":
                self._hackChat.send("@{} {}: ".format(self._nick, self._msg)
                                    + "{}".format(data["response"]))
            else:
                self._hackChat.send("@{} Sorry, I couldn't ".format(self._nick)
                                    + "find any definitions for that.")
        else:
            self._hackChat.send("@{} e.g., ".format(self._nick)
                                + "{}define hello".format(config["trigger"]))

    def _help(self):
        """Sends a message on how to use the bot."""
        joinWith = " {}".format(self._config["trigger"])
        reply = joinWith.join(sorted(self._commands))
        reply = self._config["trigger"] + reply
        if self._config["github"]:
            reply += "\nsource code: {}".format(self._config["github"])
        self._hackChat.send(
            "@{} {}".format(self._nick, reply))

    def _joiner(self):
        """Joins a channel."""
        if self._msg:
            self.join(self._msg)
        else:
            self._hackChat.send(
                "@{} joins a hack.chat channel (e.g., ".format(self._nick)
                + "{}join ben)\nYou can also ".format(config["trigger"])
                + "invite the bot via the sidebar.")

    def _joke(self):
        """Sends jokes."""
        self._hackChat.send("@{} {}".format(self._nick, jokes.yo_momma()))

    def _katex_converter(self):
        """Handles KaTeX."""
        colors = ["red", "orange", "green", "blue", "pink", "purple", "gray",
                  "rainbow"]
        sizes = ["tiny", "scriptsize", "footnotesize", "small", "normalsize",
                 "large", "Large", "LARGE", "huge", "Huge"]
        fonts = ["mathrm", "mathit", "mathbf", "mathsf", "mathtt", "mathbb",
                 "mathcal", "mathfrak", "mathscr"]
        if self._msg:
            disallowed = ("#", "$", "%", "&", "_", "{", "}", "\\", "?")
            cuccoObj = cucco.Cucco()
            newTxt = cuccoObj.replace_emojis(self._msg)
            isEmoji = False if newTxt == self._msg else True
            if set(self._msg).isdisjoint(disallowed) and not isEmoji:
                data = self._cmd.split(".")
                stringify = lambda value: value if value else ""
                size = stringify(utility.identical_item(data, sizes))
                color = stringify(utility.identical_item(data, colors))
                font = stringify(utility.identical_item(data, fonts))
                txt = katex.generator(self._msg, size, color, font)
                self._hackChat.send("@{} says {}".format(self._nick, txt))
            else:
                invalid = "\"{}\"".format("\", \"".join(disallowed))
                self._hackChat.send(
                    "@{} KaTeX doesn't support ".format(self._nick)
                    + "emoji, {}".format(invalid))
        else:
            reply = ("@{} stylizes text (e.g., ".format(self._nick)
                     + self._config["trigger"]
                     + "katex.rainbow.huge bye)\n")
            reply += "OPTIONAL COLORS: {}\n".format(", ".join(colors))
            reply += "OPTIONAL SIZES: {}\n".format(", ".join(sizes))
            reply += "OPTIONAL FONTS: {}\n".format(", ".join(fonts))
            self._hackChat.send(reply)

    def _leave(self):
        """Leaves the channel currently connected to if allowed."""
        if self._hackChat.channel in self._config["doNotLeave"]:
            self._hackChat.send("I cannot leave this channel.")
        else:
            self._hackChat.leave()

    def _math(self):
        """Solves arithmetic problems."""
        if self._msg:
            answer = arithmetic.evaluate(self._msg)
            if answer:
                self._hackChat.send("@{} {}".format(self._nick, answer))
            else:
                self._hackChat.send(
                    "@{} Sorry, I couldn't solve that.".format(self._nick))
        else:
            self._hackChat.send(
                "@{} solves math problems (e.g., (-2) ** 4)".format(self._nick)
                + "\nHow to use:\n\"+\": addition, \"-\": subtraction, \"*\": "
                + "multiplication, \"/\": division, \"//\": floor division, "
                + "\"**\": exponentiation, \"%\": remainder, \"(\" and \")\": "
                + "state order of operations")

    def _messenger(self):
        """Sends saved messages to people when they're next active."""
        info = self._cmd.split(":")
        if len(info) == 2 and info[1] and self._msg:
            data = {
                "sender": self._nick,
                "message": self._msg
            }
            messages = json.loads(open("data/messages.json").read())
            if info[1] in messages:
                messages[info[1]].append(data)
            else:
                messages[info[1]] = [data]
            with open("data/messages.json", "w") as f:
                json.dump(messages, f, indent = 4)
            self._hackChat.send(
                "@{}, @{} will get your message ".format(self._nick, info[1])
                + "the next time they message or join a channel.")
        else:
            self._hackChat.send(
                "@{} sends a message to a user the next ".format(self._nick)
                + "time they send a message or join a channel (e.g., "
                + "{}msg:ben how are you?)".format(self._config["trigger"]))

    def _poem(self):
        """Handles poetry."""
        if self._msg:
            isPoet = True if self._cmd == "poet" else False
            data = poetry.poems(self._msg, isPoet)
            if data:
                data = data[random.randint(0, len(data) - 1)]
                header = "{} by {}".format(data["title"], data["author"])
                if len(header) > 100:
                    header = "{}...".format(header[:97])
                pasted = paste.dpaste(data["poem"], title = header)
                linked = "Read the rest at {}".format(pasted["data"])
                reply = ("@{} {}\nBy: ".format(self._nick, data["title"])
                         + "{}\n{}".format(data["author"], data["poem"]))
                cut = utility.shorten_lines(reply, self._charsPerLine,
                                            self._maxLines - 1)
                self._hackChat.send(cut + linked)
            else:
                reply = "@{} Sorry, I couldn't find any poems for that."
                self._hackChat.send(reply.format(self._nick))
        else:
            if self._cmd == "poem":
                self._hackChat.send(
                    "@{} finds a poem by its name (e.g., ".format(self._nick)
                    + "{}poem sonnet)".format(self._config["trigger"]))
            else:
                self._hackChat.send(
                    "@{} finds a poem from a poet (e.g., ".format(self._nick)
                    + "{}poet shakespeare)".format(self._config["trigger"]))

    def _rate(self):
        """Handles currency conversion."""
        converted = False
        data = self._cmd.split(":") if ":" in self._cmd else None
        if data and len(data) == 3:
            fromCode = data[1].upper()
            toCode = data[2].upper()
            if fromCode and toCode:
                data = currency.convert(self._config["exchangeRateApiKey"],
                                        fromCode, toCode)
                if data["type"] == "success":
                    converted = True
                    self._hackChat.send("@{} 1 {} = {} {}".format(
                        self._nick, fromCode, data["response"], toCode))
        if not converted:
            self._hackChat.send(
                "@{} Sorry, I couldn't convert that. ".format(self._nick)
                + "(e.g., {}rate:usd:inr ".format(self._config["trigger"])
                + "gives 1 USD = 64 INR)")

    def _strengthen(self):
        """Handles passwords."""
        if self._msg:
            pwd = password.strengthen(self._msg)
            self._hackChat.send("@{} {}".format(self._nick, pwd))
        else:
            self._hackChat.send(
                "@{} strengthens a password (e.g., ".format(self._nick)
                + "{}password gum)".format(self._config["trigger"]))

    def _get_stats(self):
        """Handles statistics."""
        self._hackChat.stats()

    def _translate(self):
        """Handles translations."""
        languages = {"english": "en",
                     "spanish": "es",
                     "pedi": "nso",
                     "romanian": "ro",
                     "malay": "ms",
                     "zulu": "zu",
                     "indonesian": "id",
                     "tswana": "tn"}
        explain = True
        if self._msg and len(re.findall(":", self._cmd)) == 2:
            data = self._cmd.lower().split(":")
            if data[1] in languages and data[2] in languages:
                explain = False
                srcLang = languages[data[1]]
                targetLang = languages[data[2]]
                words = self._msg.split()
                translations = []
                for word in words:
                    lastChar = word[len(word) - 1:]
                    symbol = r"[^a-zA-Z]"
                    lastChar = lastChar if re.search(symbol, word) else ""
                    word = re.sub(symbol, "", word)
                    word = self._oxford.translate(word, targetLang, srcLang)
                    if word["type"] == "failure":
                        translations = []
                        break
                    translations.append(word["response"] + lastChar)
                if translations:
                    translated = " ".join(translations)
                    self._hackChat.send("@{} {}".format(self._nick,
                                                        translated))
                else:
                    self._hackChat.send("@{} Sorry, I ".format(self._nick)
                                        + "couldn't translate it all.")
        if explain:
            self._hackChat.send(
                "@{} supported languages: ".format(self._nick)
                + "{}\ne.g., ".format(", ".join(languages.keys()))
                + "{}".format(self._config["trigger"])
                + "translate:english:spanish I have a holiday!\n")

    def _toss(self):
        """Handles coin tosses."""
        result = "heads" if random.randint(0, 1) else "tails"
        self._hackChat.send("@{} {}".format(self._nick, result))

    def _urban(self):
        """Handles urban definitions."""
        if self._msg:
            data = dictionary.urban(self._msg)
            if data:
                reply = "@{} {}: {} ".format(self._nick, data["word"],
                                             data["definition"])
                reply = utility.shorten_lines(reply, self._charsPerLine,
                                              self._maxLines - 1)
                self._hackChat.send(reply + data["permalink"])
            else:
                self._hackChat.send(
                    "@{} Sorry, I couldn't find any ".format(self._nick)
                    + "definitions for that.")
        else:
            self._hackChat.send(
                "@{} searches Urban Dictionary (e.g., ".format(self._nick)
                + "{}urban covfefe)".format(self._config["trigger"]))


if __name__ == "__main__":
    if not os.path.exists("data"):
        os.makedirs("data")
    with open("data/afk.json", "w") as f:
        json.dump({}, f, indent = 4)
    if not os.path.isfile("data/messages.json"):
        with open("data/messages.json", "w") as f:
            json.dump({}, f, indent = 4)
    if not os.path.isfile("data/trip_codes.json"):
        with open("data/trip_codes.json", "w") as f:
            json.dump({}, f, indent = 4)
    if not os.path.isfile("data/config.json"):
        data = {}
        print("You can change your configuration later in the file "
              + "\"config.json\" located in the \"data\" folder in the "
              + "\"src\" folder. The features whose API tokens you don't "
              + "enter will remain inaccessible until you enter them.")
        data["name"] = input("\nEnter the name of the bot (e.g., myBot) "
                             + "(mandatory): ")
        print("\nA trip code is a randomly generated code based on a "
              + "password. Entering the same password gives the same trip "
              + "code each time. This allows people in anonymous chatting "
              + "sites to verify if a user is who they claim to be regardless "
              + "of their nickname.")
        data["password"] = getpass.getpass(
            "For privacy, the password won't be shown on the screen while "
            + "you're typing. Enter the password (e.g., myPassword) "
            + "(optional): ")
        print("\nChannels are chats on https://hack.chat. If the channel for "
              + "the name you enter doesn't exist, one will automatically be "
              + "created. To join the \"math\" channel "
              + "(i.e., https://hack.chat/?math), enter \"math\".)")
        channels = input(
            "Enter a space-separated list of the channels the bot should  "
            + "connect to on start-up (e.g., botDev programming) "
            + "(mandatory): ")
        data["channels"] = channels.split()
        print("\nFor the bot to know when it's being called, you must state a "
              + "trigger.")
        data["trigger"] = input("Enter the trigger (e.g., \".\" will trigger "
                                + "the bot for \".help\") (mandatory): ")
        url = input("\nEnter the websocket URL of the hack.chat instance to "
                    + "connect to (not stating one will enter the original "
                    + "sites' websocket URL) (optional): ")
        data["url"] = url if url else "wss://hack.chat/chat-ws"
        data["oxfordAppId"] = input("\nEnter the Oxford Dictionaries API app "
                                    + "id (optional): ")
        data["oxfordAppKey"] = input("Enter the Oxford Dictionaries API app "
                                     + "key (optional): ")
        data["exchangeRateApiKey"] = input("\nEnter the currency converter "
                                           + "API key (optional): ")
        data["github"] = input("\nEnter the link to the GitHub repository "
                               + "this is on (optional): ")
        channels = input(
            "\nEnter a space-separated list of the channels the bot cannot "
            + "leave (e.g., botDev programming) (optional): ")
        data["doNotLeave"] = channels.split()
        print()
        with open("data/config.json", "w") as f:
            json.dump(data, f, indent = 4)
    config = json.loads(open("data/config.json").read())
    bot = HackChatBot()
    _ = ("The bot will wait 30 seconds before joining each new channel to "
         + "prevent getting ratelimited.")
    msg = utility.date_format("info", _)
    print("\n{}".format(msg))
    for channel in config["channels"]:
        threading.Thread(target = bot.join(channel)).start()
        _ = "The bot joined the channel: {}".format(channel)
        msg = utility.date_format("info", _)
        print("\n{}".format(msg))
        time.sleep(30)

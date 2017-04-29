#!/usr/bin/env python3

import datetime
import random
import re

import hackchat

import settings
from commands import get_poem, quotes, youtube


random.seed(datetime.datetime.now())
chat = hackchat.HackChat(settings.name + "#" + settings.tripcode, settings.channel)


def message_got(chat, message, sender):
    """Checks messages on https://hack.chat and responds to ones triggering the bot."""
    trigger = "."
    msg = message.strip().lower()
    space = re.search(r"\s", msg)
    if msg[:1] == trigger:
        cmd = msg[1:space.start()] if space else msg[1:]
        arg = msg[space.end():] if space else False
        notFound = "Sorry, I couldn't find any {} for that."
        valid = True
        if cmd == "poem" or cmd == "poet":
            if arg:
                data = get_poem.get_poem(arg, True if cmd == "poet" else False)
                if data == None:
                    reply = notFound.format("poems")
                else:
                    poem = data[0].split("\n")
                    lines = 0
                    reply = ""
                    for line in poem:
                        reply += line + "\n"
                        lines += 1
                        if lines == 7:
                            reply += data[1]
                            break
            else:
                reply = "e.g. " + trigger + ("poem daffodils" if cmd == "poem" else "poet shakespeare")
        elif cmd == "quote":
            if arg:
                data = quotes.quotes(arg)
                if data:
                    reply = data[random.randint(0, len(data) - 1)]
                else:
                    reply = notFound.format("quotes")
            else:
                reply = "e.g. {}quote buddha".format(trigger)
        elif cmd == "h" or cmd == "help":
            commands = sorted(("about", "h", "help", "yt", "poem", "poet", "toss", "quote"))
            reply = ""
            for cmd in commands:
                reply += " " + trigger + cmd
            reply =  reply[1:]
        elif cmd == "about":
            reply = ("Creator: Neel Kamath https://github.com/neelkamath\n" +
                     "Code: https://github.com/neelkamath/hack.chat-bot\n" +
                     "Language: Python\n" +
                     "Website: https://neelkamath.github.io\n")
        elif cmd == "yt":
            if arg:
                count = 0
                videos = youtube.videos(arg)
                if videos:
                    reply = ""
                    for video in videos:
                        reply += video + "\n" + videos[video] + "\n"
                        count += 1
                        if count == 3:
                            break
                else:
                    reply = notFound.format("videos")
            else:
                reply = "searches YouTube e.g. {}yt star wars trailer".format(trigger)
        elif cmd == "toss":
            reply = "heads" if random.randint(0, 1) == 1 else "tails"
        else:
            valid = False
        if valid:
            chat.send_message("@{} ".format(sender) + reply)


chat.on_message.append(message_got)
chat.start_ping_thread()
chat.run_loop()

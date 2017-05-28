#!/usr/bin/env python3

import json
import re
import time
import threading
import websocket


class HackChat:
    """This class sends and receives data on a channel on https://hack.chat.

    Keyword arguments:
    callback -- function; the name of the function to receive data sent from https://hack.chat
    channel -- string; the channel on https://hack.chat to connect to
    nick -- string; the nickname to use upon connecting
    pwd -- string; the password that generates you a tripcode upon entering

    Usage:
    Access the <onlineUsers> property to get a list of the users currently online in the channel.
    The data received by the callback function will be a dictionary having one of the following formats:
    {
        "type": "message",
        "nick": <senders' nickname>,
        "text": <senders' message>,
        "trip": <senders' tripcode if the sender has one>
    }
    {
        "type": "onlineAdd",
        "nick": <nickname of user who just joint the channel>
    }
    {
        "type": "onlineRemove",
        "nick": <nickname of user who just left the channel>
    }
    {
        "type": "invite",
        "nick": <nickname of user who invited you to a channel (might be your own if you invited someone else)>,
        "channel": <name of the channel invited to>
    }
    {
        "type": "stats",
        "IPs": <number of unique IPs connected to https://hack.chat>,
        "channels": <number of channels in use on https://hack.chat>
    }
    {
        "type": "warn",
        "warning": <explanation of why you have been warned (e.g., nickname you used is already taken)>
    }

    Example:
        import connection


        def on_message(connector, data): # Make a callback function with two parameters.
            print(data) # The second parameter (<data>) is the data received.
            print(connector.onlineUsers)
            if "onlineAdd" in data: # Check if someone joined the channel.
                connector.send("Hello {}".format(data["onlineAdd"])) # Greet the person joining the channel.


        if __name__ == "__main__":
            connection.HackChat(on_message, "bottest", "myBot")
    """

    def __init__(self, callback, channel, nick, pwd = ""):
        """This function initializes values."""
        self.callback = callback
        self.channel = channel
        self.nick = nick
        self.pwd = pwd
        self.onlineUsers = []
        self._ws = websocket.create_connection("wss://hack.chat/chat-ws")
        self._ws.send(json.dumps({"cmd": "join", "channel": self.channel, "nick": "{}#{}".format(self.nick, self.pwd)}))
        threading.Thread(target = self._ping).start()
        threading.Thread(target = self._run).start()

    def _ping(self):
        """This function periodically pings the server to retain the websocket connection."""
        while True:
            time.sleep(60)
            self._ws.send(json.dumps({"cmd": "ping"}))

    def _run(self):
        """This function sends and receives data from https://hack.chat to the callback function."""
        while True:
            result = json.loads(self._ws.recv())
            if result["cmd"] == "chat":
                data = {"type": "message", "nick": result["nick"], "text": result["text"]}
                if "trip" in result:
                    data["trip"] = result["trip"]
                self.callback(self, data)
            elif result["cmd"] == "onlineSet":
                self.onlineUsers += result["nicks"]
            elif result["cmd"] == "onlineAdd":
                self.onlineUsers.append(result["nick"])
                self.callback(self, {"type": "onlineAdd", "nick": result["nick"]})
            elif result["cmd"] == "onlineRemove":
                self.onlineUsers.remove(result["nick"])
                self.callback(self, {"type": "onlineRemove", "nick": result["nick"]})
            elif result["cmd"] == "info" and " invited " in result["text"]:
                if "You invited " in result["text"]:
                    name = self.nick
                else:
                    space = re.search(r"\s", result["text"])
                    name = result["text"][:space.start()]
                link = re.search("\?", result["text"])
                channel = result["text"][link.end():]
                self.callback(self, {"type": "invite", "nick": name, "channel": channel})
            elif result["cmd"] == "info" and " IPs " in result["text"]:
                data = result["text"].split()
                self.callback(self, {"type": "stats", "IPs": data[0], "channels": data[4]})
            elif result["cmd"] == "warn":
                self.callback(self, {"type": "warn", "warning": result["text"]})

    def send(self, msg):
        """Use this to send a message <msg> (string) to the channel connected."""
        self._ws.send(json.dumps({"cmd": "chat", "text": msg}))

    def invite(self, nick):
        """This sends an invite to the person <nick> (string) to join a randomly generated channel.

        This invite will only be visible to <nick>. The callback function will receive the data such as the channel.
        """

        self._ws.send(json.dumps({"cmd": "invite", "nick": nick}))

    def stats(self):
        """This sends the number of unique IPs and channels on https://hack.chat to the callback function."""
        self._ws.send(json.dumps({"cmd": "stats"}))

import re
import urllib
import requests
import threading
import configparser

# Bot
from . import botserver as server

from .botserver import telegrambot
from .botserver import kikbot
from .botserver import facebookbot
from .botserver import htmlbot


# Read config file
config = configparser.ConfigParser()
config.read('config.ini')

NAME = config["general"]["name"]

serv = server.ServerHelper()

Regex = serv.vagueReply.regex

class MyAnonymousBot(server.Bot):
    

    hearts = [":red_heart:", ":green_heart:", ":black_heart:", ":blue_heart:", ":purple_heart:", ":yellow_heart:"]

    yes = serv.vagueReply.new("positive", hearts+["yes", "ya", "yea", "yeah", "sure", "of course", "ok", "okay", ":thumbs_up:", ":OK_hand:", ":OK_button:", ":COOL_button:", ":heavy_check_mark:", ":white_heavy_check_mark:", ":ballot_box_with_check:"])
    no = serv.vagueReply.new("negative", [Regex("no+"), ":thumbs_down:", ":cross_mark:", ":cross_mark_button:", ":heavy_multiplication_x:", ":no_entry:", ":prohibited:", ":broken_heart:"])

    
    startMessageText = """Welcome to """+NAME
    startMessageText_full = startMessageText+"""
Hi. Nice to meet you."""

    def __init__(self, serv, name):
        super().__init__(serv, name)
        self.availableUsers = []
        self.connectedUsers = []
        self.__movingUsersLock = threading.Lock()

    # Builtin event: called if no other function matches
    def onOtherResponse(self, msg):
        user = self.user(msg)
        
        chatactive = user.retrieveValue("chatactive", False)
        
        if chatactive:
            # Find second user
            with self.__movingUsersLock:
                user2 = None
                for pair in self.connectedUsers:
                    if user in pair:
                        user2 = pair[0] if user == pair[1] else pair[1]
                        break
                
                if user2 is not None:
                    # Relay message to second user
                    print()
                    return self.sendText(user2, msg["text"])
        
        self.sendText(msg, "Ok. not sure what to do with it")
        
        

    def what(self, msg):
        self.sendText(msg, "Whaaaaat?")

    @serv.textLike("/start")
    def commandStart(self, msg):
        # Show the welcome message
        self.sendText(msg, self.startMessageText_full)
        
        self.sendQuestionWithReplies(msg, "Please send me a username you would like", onOtherResponse=self.commandSetUsername)
        
    
    @serv.textStartsWith("/username")
    @serv.textStartsWith("/name")
    def commandSetUsername(self, msg):
        # Set the username
        
        user = self.user(msg)
        username = user.retrieveValue("username")
        
        query = msg["text"]
        if msg["text_nice_lower"].startswith("/username"):
            query = query[len("/username"):]
        if msg["text_nice_lower"].startswith("/name"):
            query = query[len("/name"):]
        query = query.strip()
            
        if query == "":
            if username is not None:
                self.sendText(msg, "Your current username is %s" % username)
            else:
                self.sendQuestionWithReplies(msg, "Invalid username, try something else.", onOtherResponse=self.commandSetUsername)
        else:
            # Save name
            user.storeValue("username", query)
            self.sendText(msg, "Your new username is %s" % query)
            user.clearResponses()
            self.commandFindNewChat(msg)
    
    @serv.textLike("/new")
    def commandFindNewChat(self, msg):
        user = self.user(msg)
        username = user.retrieveValue("username")
        if username is None:
            return self.commandStart(msg);
            
            
        chatactive = user.retrieveValue("chatactive", False)
        if chatactive:
            return self.sendText(msg, "First, please /leave the current chat.")
        
        with self.__movingUsersLock:
            if user in self.availableUsers:
                self.availableUsers.remove(user) # Make sure the user is not already waiting
            
            if len(self.availableUsers) == 0:
                self.sendText(msg, "Nobody is available. Please wait for another person to join.")
                self.availableUsers.append(user)
                
            else:
                # Connect 
                user2 = self.availableUsers.pop(0)
                
                user.storeValue("chatactive", True)
                user2.storeValue("chatactive", True)
                
                self.connectedUsers.append((user, user2))
                
                
                username2 = user2.retrieveValue("username")
                self.sendText(msg, "You are now chatting with %s\nLeave the chat with /leave" % username2)
                self.sendText(user2, "You are now chatting with %s\nLeave the chat with /leave" % username)
        user.clearResponses()
            
            
    @serv.textLike("/leave")
    def commandLeave(self, msg):
        user = self.user(msg)
        
        chatactive = user.retrieveValue("chatactive", False)
        
        if chatactive:
            with self.__movingUsersLock:
                # Find second user
                user2 = None
                for pair in self.connectedUsers:
                    if user in pair:
                        user2 = pair[0] if user == pair[1] else pair[1]
                        self.connectedUsers.remove(pair)
                        break
                
                if user2 is not None:
                    # Relay message to second user
                    self.sendText(user2, "#### %s left the chat." % user.retrieveValue("username"))
                    user2.storeValue("chatactive", False)
                self.sendText(msg, "#### You left the chat.")
            user.storeValue("chatactive", False)
                
                
            
            
    @serv.textLike("/help")
    @serv.textLike("help")
    def showHelp(self, msg):
        self.sendText(msg, """This bot enables you to chat anonymously with other people. It works on Telegram, Kik and Facebook Messenger. 
/new  - Start a new chat
/leave - Leave the current chat
/about - Info about this bot
/username {name} - Choose a username""")
        
    
    @serv.textLike("/about")
    @serv.textLike("about")
    def showAbout(self, msg):
        self.sendText(msg, "This bot enables you to chat anonymously with other people. It works on Telegram, Kik and Facebook Messenger. ")


def getMyBot(HOSTNAME):
    # Run all bots
    myBot = MyAnonymousBot(serv, NAME)
        
    if "telegrambot" in config:
        myBot.addFlaskBot(bottype=telegrambot.TelegramBot, route=config["telegrambot"]["route"], token=config["telegrambot"]["token"], webhook_host=HOSTNAME)
    
    if "kikbot" in config:
        myBot.addFlaskBot(bottype=kikbot.KikBot, route=config["kikbot"]["route"], name=config["kikbot"]["name"], apikey=config["kikbot"]["apikey"], webhook_host=HOSTNAME)
        
    if "facebookbot" in config:
        myBot.addFlaskBot(bottype=facebookbot.FacebookBot,
                          route=config["facebookbot"]["route"],
                          app_secret=config["facebookbot"]["app_secret"],
                          verify_token=config["facebookbot"]["verify_token"],
                          access_token=config["facebookbot"]["access_token"],
                          start_message=myBot.startMessageText)
                          
    if "htmlbot" in config:
        myBot.addFlaskBot(bottype=htmlbot.HtmlBot, route=config["htmlbot"]["route"])
    
    return myBot

    
def getMyBot_html():
    # Only run the HMTL bot for easier local testing
    myBot = MyAnonymousBot(serv, NAME)
        
    if "htmlbot" in config:
        myBot.addFlaskBot(bottype=htmlbot.HtmlBot, route=config["htmlbot"]["route"])
    
    return myBot
    
    

if __name__ == '__main__':
    getMyBot_html().run(port=80) # http://127.0.0.1:80/chat


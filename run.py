import os
from AnonymousBot import getMyBot

def homepage():
    return "Running", 200

port = int(os.environ.get('PORT', 33507))

myBot = getMyBot(HOSTNAME=r"https://chatanonymously.herokuapp.com")

myBot.getFlask().route("/", methods=['GET'], endpoint="routeHomepage")(homepage)

myBot.run(host='0.0.0.0', port=port)

import requests
from bs4 import BeautifulSoup
import discord
import asyncio
from dotenv import dotenv_values

currentTrackers = set()

token = dotenv_values(".env")["TOKEN"]

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

class Tracker:
    def __init__(self, crn, term, id, user):
        self.crn = crn
        self.term = term
        self.url = "https://oscar.gatech.edu/bprod/bwckschd.p_disp_detail_sched?term_in="
        self.url += str(self.term) + '&crn_in=' + str(self.crn)
        self.id = id
        self.user = user
        self.task = asyncio.get_event_loop().create_task(self.doRun())
    
    def isNotifiction(self):
        with requests.Session() as s:
            with s.get(self.url) as r:
                soup = BeautifulSoup(r.content, 'html.parser')
                table = soup.find_all('table', class_="datadisplaytable")
                seating = table[1].findAll('td', class_="dddefault")
                if (int(seating[2].string) <= 0):
                    return False
                else:
                    return True

    def __hash__(self):
        return int(self.id)

    def __eq__(self, other):
        return self.id == other.id
    
    def mount(self):
        asyncio.get_event_loop().run_until_complete(self.task)

    def unmount(self):
        self.task.cancel()

    async def doRun(self):
        while True:
            s = requests.Session()
            r = s.get(self.url)
            soup = BeautifulSoup(r.content, 'html.parser')
            name = soup.find_all('th', class_="ddlabel")[0]
            table = soup.find_all('table', class_="datadisplaytable")
            seating = table[1].findAll('td', class_="dddefault")
            if (int(seating[2].string) > 0 and int(seating[4].string) < int(seating[2].string)):
                user = await client.fetch_user(self.user)
                await user.send("Spots open in: " + str(name))
            await asyncio.sleep(15)

@client.event
async def on_message(message: discord.Message):
    user_id = message.author.id
    if (len(message.content) > 0):
        if (message.content[0] != '!'):
            return
        if ("add" in message.content):
            split_message = message.content.split(" ")
            crn = split_message[1]
            term = split_message[2]
            tracker_id = str(user_id) + crn + term
            tracker = Tracker(int(crn), int(term), tracker_id, user_id)
            if (tracker not in currentTrackers):
                currentTrackers.add(tracker)
                tracker.mount()
        elif ("remove" in message.content):
            split_message = message.content.split(" ")
            crn = split_message[1]
            term = split_message[2]
            tracker_id = str(user_id) + crn + term
            for tracker in currentTrackers:
                if (tracker.id == tracker_id):
                    tracker.unmount()
                    currentTrackers.remove(tracker)
                    return
    return 

client.run(token)
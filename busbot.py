import discord
import asyncio
import urllib.request
from urllib.request import urlopen
import json
import time, datetime
import pytz
import dateutil.parser
from secrets import DISCORD_APP_BOT_TOKEN, LTA_DATAMALL_ACCOUNT_KEY

client = discord.Client()

@client.event
@asyncio.coroutine 
def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

@client.event
@asyncio.coroutine
def on_message(message):
    if message.content.startswith('!nextbus') | message.content.startswith('t!nextbus'):
        if len(message.content.split(" ")) == 2 and len(message.content.split(" ")[1]) == 5:
            busStopNumber = message.content.split(" ")[1]
            for i in get_next_bus_arrival(busStopNumber):
                yield from client.send_message(message.channel, i)
                #continue
        else:
            yield from client.send_message(message.channel, "The correct usage is `!nxtbus <Bus stop number>`.")


def calculate_time_left(estimated):
    later = dateutil.parser.parse(estimated).timestamp()
    now = datetime.datetime.now(pytz.utc).timestamp()
    return "{:.1f}".format((later-now)/60)

def show_loading(loading):
    icons = {
        "Seats Available": ":green_heart:",
        "Standing Available": ":yellow_heart:",
        "Limited Standing": ":broken_heart:"
    }
    return icons[loading]

def show_feature(feature):
    x = ""
    if feature == "WAB":
        x = ":wheelchair:"
    return x
    
def get_next_bus_arrival(busStopCode):
    try:
        #if busStopCode[0] == '0':
            #busStopCode = busStopCode[1:5]
        requestUrl = "http://datamall2.mytransport.sg/ltaodataservice/BusArrival?BusStopID=" + busStopCode
        webRequest = urllib.request.Request(requestUrl, None, {'AccountKey': LTA_DATAMALL_ACCOUNT_KEY, 'acccept': 'application/json'})
        webResponse = urllib.request.urlopen(webRequest)

        data = json.loads(webResponse.readall().decode('utf-8'))

        titleStr = ":bus: **Next Bus Arrivals** | :busstop: {} | :clock1: Updated {}hrs\n".format(busStopCode, time.strftime("%H%M", time.localtime()))
        serviceInfo = []
        servicesNotOperating = []

        for x in data["Services"]:
            serviceNo = x["ServiceNo"]
            inOperation = (x["Status"] == "In Operation")
            if(not inOperation):
                #svcStr += ":x: _Not operating_ "
                servicesNotOperating += [serviceNo]
            else:
                svcStr = "Service **{}**: ".format(serviceNo)
                for b in ["NextBus", "SubsequentBus", "SubsequentBus3"]:
                    if x[b]["EstimatedArrival"] != "":
                        estArrival = calculate_time_left(x[b]["EstimatedArrival"])
                        loading = show_loading(x[b]["Load"])
                        feature = show_feature(x[b]["Feature"])
                        svcStr += "{} mins {}{} ".format(estArrival, loading, feature)
                serviceInfo += [svcStr]
        
        serviceInfo = sorted(serviceInfo)
               
        if len(servicesNotOperating) > 0:
            notOperatingStr = ":x: Not operating now: "
            for x in sorted(servicesNotOperating):
                notOperatingStr += "{} ".format(x)
            serviceInfo += [notOperatingStr]
        
        print("DATA RETURNED")

        results = [titleStr]

        for i in serviceInfo:
            seperator = "\n"
            if len(results[-1]) + len(seperator) +  len(i) >= 2000:
                results += ["*(Continued - page {})*\n".format(len(results)+1)]
            results[-1] += seperator
            results[-1] += i

        print("Returned results for {}. Pages: {}. ".format(busStopCode, str(len(results))))
        for i in results:
            print(len(i))
        return results
    except:
        return ["An error was encountered."]

client.run(DISCORD_APP_BOT_TOKEN) #Token


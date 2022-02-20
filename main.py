import base64
import requests
from keep_alive import keep_alive

import discord
from discord.ext import commands
from discord import guild
from discord_slash import SlashCommand, SlashContext
from discord_slash.utils.manage_commands import create_choice, create_option
from discord import DMChannel
import os
import requests
import json
import time
import re
from replit import db
import asyncio
import math
import urllib.request

#https://stackoverflow.com/questions/38491722/reading-a-github-file-using-python-returns-html-tags
'''
url = 'https://raw.githubusercontent.com/DesmoSearch/DesmoSearch/main/data/thetitles.json'
req = requests.get(url)
if req.status_code == requests.codes.ok:
    req = req.json()
    print(len(req))
    db['thetitles']=req
else:
    print('Content was not found.')
'''

print(db.keys())
ParentGraphsList=db['ParentGraphsList']
thetitles=db['thetitles']
GraphsList=db['GraphsList']
objowner=db['objowner']
noofresults=5;

client = commands.Bot(command_prefix="_")
slash = SlashCommand(client, sync_commands=True)
token = os.environ.get("DISCORD_BOT_SECRET")

@client.event
async def on_ready():
  await client.change_presence(activity=discord.Game(name=f"on {len(client.guilds)} servers | {db['searches']} searches done!"))

@client.event
async def on_message(message): 
  pattern=re.compile(r"!desmos ([a-zA-Z0-9 ]{3,}|\/.*?\/)(?: *\?(?:(title|hash|owner)(?:=([a-zA-Z0-9 ]{3,}|\/.*?\/))?)(?:&(title|hash|owner)(?:=([a-zA-Z0-9 ]{3,}|\/.*?\/))?)?(?:&(title|hash|owner)(?:=([a-zA-Z0-9 ]{3,}|\/.*?\/))?)?)?")
  x=pattern.finditer(message.content)
  if message.author == client.user:
    return
  elif len(list(x))==1:

    db['searches']=db['searches']+1
    await on_ready()
    await dmsend(repr(message)+"\n\n"+message.content)
    
    searchterm=[ii.group(1) for ii in pattern.finditer(message.content)][0]
    parameterterm = [[ii.group(iii) for ii in pattern.finditer(message.content)][0] for iii in [2,4,6]]
    searchterm1=[ii.group(3) for ii in pattern.finditer(message.content)][0]
    searchterm2=[ii.group(5) for ii in pattern.finditer(message.content)][0]
    searchterm3=[ii.group(7) for ii in pattern.finditer(message.content)][0]
    if checkIfDuplicates(parameterterm):
      parameterterm=[None,None,None]
      searchterm1=""
      searchterm2=""
      searchterm3=""

    titlecond = True if parameterterm==[None,None,None] else ('title' in parameterterm)
    ownercond = True if parameterterm==[None,None,None] else ('owner' in parameterterm)
    hashcond = True if parameterterm==[None,None,None] else ('hash' in parameterterm)
    
    if "/" in searchterm:
      searchterm=searchterm[1:-1]
    if searchterm1 is None:
      searchterm1 = ""
    elif "/" in searchterm1:
      searchterm1=searchterm1[1:-1]

    if searchterm2 is None:
      searchterm2 = ""
    elif "/" in searchterm2:
      searchterm2=searchterm2[1:-1]

    if searchterm3 is None:
      searchterm3 = ""
    elif "/" in searchterm3:
      searchterm3=searchterm3[1:-1]
    
    print(f'"{searchterm}"')

    searchterm0sub=[searchterm1,searchterm2,searchterm3]
    searchtermtitle, searchtermhash, searchtermowner = "", "", "" 
    try:
      searchtermtitle=searchterm0sub[parameterterm.index('title')]
    except ValueError:
      searchtermtitle=""
    try:
      searchtermhash=searchterm0sub[parameterterm.index('hash')]
    except ValueError:
      searchtermhash=""
    try:
      searchtermowner=searchterm0sub[parameterterm.index('owner')]
    except ValueError:
      searchtermowner=""

    searchresult = [hash for hash, title in thetitles.items() if (titlecond*bool(re.search(searchterm, str(title))) or hashcond*bool(re.search(searchterm, str(hash))) or ownercond*bool(re.search(searchterm, str(objowner.get(str(hash),None))))) and (bool(re.search(searchtermtitle, str(title))) and bool(re.search(searchtermhash, str(hash))) and bool(re.search(searchtermowner, str(objowner.get(str(hash),None)))))]

    #https://gist.github.com/noaione/58cdd25a1cc19388021deb0a77582c97
    max_page=math.ceil(len(searchresult)/noofresults)
    first_run = True
    num = 1
    Gnum = 1
    GnumDisplay=0
    while True:
        if first_run:
            first_run = False
            msg = await message.channel.send(embed=createembed(-1,num,searchresult,max_page,message))

        reactmoji = []

        if max_page == 1 and num == 1:
            pass
        elif num == 1:
            reactmoji.append('⏩')
        elif num == max_page:
            reactmoji.append('⏪')
        elif num > 1 and num < max_page:
            reactmoji.extend(['⏪', '⏩'])

        if len(searchresult) == 1 and Gnum == 0:
            pass
        elif Gnum == 1:
            reactmoji.append('🔽')
        elif num == len(searchresult) and Gnum-noofresults*(num-1)>0:
            reactmoji.append('🔼')
        elif Gnum > 1 and num < len(searchresult):
            reactmoji.extend(['🔼', '🔽'])

        reactmoji.append('✅')
        if str(message.author.id)=='686012491607572515':
           reactmoji.append('❌')
  
        for react in reactmoji:
            await msg.add_reaction(react)
            

        def check_react(reaction, user):
            if reaction.message.id != msg.id:
                return False
            if user != message.author:
                return False
            if str(reaction.emoji) not in reactmoji:
                return False
            return True

        try:
            res, user = await client.wait_for('reaction_add', timeout=100.0, check=check_react)
        except asyncio.TimeoutError:
            return await msg.clear_reactions()
        if user != message.author:
            pass
        elif '⏪' in str(res.emoji):
            num = num - 1
            Gnum = (num-1)*noofresults+1
            GnumDisplay=0
            await msg.clear_reactions()
            await msg.edit(embed=createembed(-1,num,searchresult,max_page,message))
        elif '⏩' in str(res.emoji):
            num = num + 1
            Gnum = (num-1)*noofresults+1
            GnumDisplay=0
            await msg.clear_reactions()
            await msg.edit(embed=createembed(-1,num,searchresult,max_page,message))
        elif '🔽' in str(res.emoji):
            Gnum  = Gnum if GnumDisplay==0 else Gnum+1
            GnumDisplay=1
            num = math.ceil(Gnum/noofresults)
            await msg.clear_reactions()
            await msg.edit(embed=createembed(Gnum,num,searchresult,max_page,message))
        elif '🔼' in str(res.emoji):
            Gnum  = Gnum if GnumDisplay==0 else Gnum-1
            GnumDisplay=1
            num = math.ceil(Gnum/noofresults)
            await msg.clear_reactions()
            await msg.edit(embed=createembed(Gnum,num,searchresult,max_page,message))
        elif '✅' in str(res.emoji):
            return await msg.clear_reactions()
        elif '❌' in str(res.emoji):
            await message.delete()
            return await msg.delete()

    
def createembed(Gnum,num,result,max_page,message):
  datahashes=result[noofresults*(num-1):noofresults*num+1]
  thedescription="".join(f'{"> __**" if Gnum==(num-1)*noofresults+i+1 else ""}{(num-1)*noofresults+i+1}. "{str(objowner.get(str(datahashes[i]),None))}": [{thetitles[datahashes[i]]}](https://www.desmos.com/calculator/{datahashes[i]}){"**__" if Gnum==(num-1)*noofresults+i+1 else ""}\n'for i in range(len(datahashes)))
  
  pattern2=re.compile(r"!desmos (([a-zA-Z0-9 ]{3,}|\/.*?\/)(?: *\?(?:(title|hash|owner)(?:=([a-zA-Z0-9 ]{3,}|\/.*?\/))?)(?:&(title|hash|owner)(?:=([a-zA-Z0-9 ]{3,}|\/.*?\/))?)?(?:&(title|hash|owner)(?:=([a-zA-Z0-9 ]{3,}|\/.*?\/))?)?)?)")
  searchterm=[ii2.group(1) for ii2 in pattern2.finditer(message.content)][0]
  embed = discord.Embed(color=0x19212d, title=str(len(result))+" graphs for \""+searchterm+"\"",description=thedescription)
  embed.set_author(name=str(message.author), icon_url=message.author.avatar_url)
  embed.set_footer(text="Page: "+str(num)+"/"+str(max_page))
  if Gnum>-1:
    dahash=result[Gnum]
    #dainfo=getinfo("https://www.desmos.com/calculator/"+dahash)
    embed.set_image(url=f"https://saved-work.desmos.com/calc_thumbs/production/{dahash}.png")
    embed.add_field(name="Graph Selected:", value=f"https://www.desmos.com/calculator/{dahash}", inline=False)
    if objowner.get(str(dahash),None) is not None:
      embed.add_field(name="Possible Author", value=objowner.get(str(dahash),None), inline=False)
    #embed.add_field(name="Date Created", value=dainfo['date'], inline=False)
  return embed
  
async def dmsend(msg):
    user = await client.fetch_user("686012491607572515")
    await DMChannel.send(user,"```"+msg+"```")

def checkIfDuplicates(listOfElems):
    ''' Check if given list contains any duplicates '''
    listOfElems=list(filter((None).__ne__, listOfElems))
    if len(listOfElems) == len(set(listOfElems)):
        return False
    else:
        return True

def getinfo(url):
  fp = urllib.request.urlopen(url)
  mybytes = fp.read()
  
  mystr = mybytes.decode("utf8")
  fp.close()
  patternparent = re.compile(r"quot;parent_hash&quot;:&quot;([a-z0-9]{10,20})&quot;")
  parentGraph=None if len(list(patternparent.finditer(mystr)))==0 else [ii.group(1) for ii in patternparent.finditer(mystr)][0]
  patterndate = re.compile(r"created&quot;:&quot;(.*?)&quot")
  dateofGraph=[ii.group(1) for ii in patterndate.finditer(mystr)][0]
  patternnote = re.compile(r"&quot;text&quot;:&quot;(.*?)&quot")
  notes=None if len(list(patternnote.finditer(mystr)))==0 else [ii.group(1) for ii in patternnote.finditer(mystr)]
  patternfolder = re.compile(r"&quot;type&quot;:&quot;folder&quot;,&quot;id&quot;:&quot;[0-9]*&quot;,&quot;title&quot;:&quot;(.*?)&quot;")
  folders=None if len(list(patternfolder.finditer(mystr)))==0 else [ii.group(1) for ii in patternfolder.finditer(mystr)]
  patternvar = re.compile(r";(.(?:_{?\w*}?)?)=")
  variables=None if len(list(patternvar.finditer(mystr)))==0 else [ii.group(1) for ii in patternvar.finditer(mystr)]
  return {"parentGraph":parentGraph,"date":dateofGraph,"folders":folders,"notes":notes,"variables":list(set(variables))}

keep_alive()
client.run(token)
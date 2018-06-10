# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import re
import random
import json
import urllib.request
import urllib.parse

from telethon import events

pats = []
oops = "OOPSIE WOOPSIE!! Uwu We madea fucky wucky!! A wittle fucko boingo! " \
       "The code monkeys at our headquarters are working VEWY HAWD to fix " \
       "this!"


@borg.on(events.NewMessage)
async def on_pat(event):
    if event.forward:
        return

    user = borg.me.username

    if not user or not re.match(fr"(?i)/headpat@{user}", event.raw_text):
        return

    global pats
    if not pats:
        try:
            pats = json.loads(urllib.request.urlopen(urllib.request.Request(
                "http://headp.at/js/pats.json",
                headers={"User-Agent": "Mozilla/5.0 (X11; U; Linux i686) "
                                       "Gecko/20071127 Firefox/2.0.0.11"}
            )).read().decode("utf-8"))
        except Exception as e:
            print(e)
            await event.reply(oops)
            return

    choice = urllib.parse.quote(random.choice(pats))
    await event.reply(f"[Pat!](https://headp.at/pats/{choice})")

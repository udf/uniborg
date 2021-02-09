"""Quotes

Add a quote to the database with `/quote` and recall with `/recall search term`.
It only works with messages sent to a group by a user (no forwards).
Quotes are recalled with the text, the sender's name, and date it was originally sent.

patterns:
 • `q(uote)?|cite`
 • `(r(ecall)?|(get|fetch)quote)(?: ([\s\S]+))?`
"""

from random import choice
from asyncio import sleep
from telethon import types

import logging
logging.basicConfig(level=logging.WARNING)

@borg.on(borg.cmd(r"q(uote)?|cite"))
async def quote(event):
    if event.is_private and not event.is_reply:
        return

    reply_msg = await event.get_reply_message()
    if reply_msg.fwd_from:
        return

    text = reply_msg.text
    if not text:
        return

    chat = str(event.chat_id)
    sender = await reply_msg.get_sender()
    if isinstance(sender, types.Channel) or sender.bot:
        return

    quote = {}

    quote["id"] = str(reply_msg.id)
    quote["text"] = text
    quote["sender"] = sender
    quote["date"] = reply_msg.date

    quotes = storage.quotes or {}
    try:
        for q in quotes[chat]:
            if quote["id"] == q["id"]:
                msg = await event.reply("Duplicate quote in database")
                await sleep(10)
                await msg.delete()
                return
    except KeyError:
        pass

    try:
        quotes[chat].append(quote)
    except KeyError:
        quotes[chat] = [quote]
    storage.quotes = quotes

    await event.respond(f"Quote saved!  (ID:  `{reply_msg.id}`)")


@borg.on(borg.cmd(r"(r(ecall)?|(get|fetch)quote)(?: (?P<phrase>[\s\S]+))?"))
async def recall(event):
    if event.is_private:
        return

    phrase = event.pattern_match["phrase"]
    chat = str(event.chat_id)

    match_quotes = []
    quotes = storage.quotes or {}

    try:
        quotes[chat]
    except KeyError:
        return

    if not phrase:
        match_quotes = quotes[chat]
    else:
        phrase = phrase.lower()
        for q in quotes[chat]:
            id = q["id"]
            text = q["text"].lower()
            sender = q["sender"]
            first_name = sender.first_name.lower()
            last_name = (sender.last_name or "").lower()

            if phrase == id:
                match_quotes.append(q)
                break
            if phrase in text:
                match_quotes.append(q)
                continue
            if phrase in first_name:
                match_quotes.append(q)
                continue
            if phrase in last_name:
                match_quotes.append(q)
                continue


    if not match_quotes:
        return
    quote = choice(match_quotes)

    id = quote["id"]
    text = quote["text"]
    sender = quote["sender"]
    sender_name = f"{sender.first_name} {sender.last_name or ''}"
    msg_date = (quote["date"]).strftime("%B, %Y")

    format_quote = f"<b>{text}</b>"
    format_quote += f"\n<i>- <a href='tg://user?id={sender.id}'>{sender_name}</a>, "
    format_quote += f"<a href='t.me/share/url?url=%2Frecall+{id}'>{msg_date}</a></i>"
    # format_quote += f" #qid{id}"

    msg = await event.respond(format_quote, parse_mode="html")

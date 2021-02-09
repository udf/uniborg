"""Quotes

Add a quote to the database with `/quote` and recall with `/recall search term`.
It only works with messages sent to a group by a user (no forwards).
Quotes are recalled with the text, the sender's name, and date it was originally sent.

patterns:
 • `q(uote)?|cite`
 • `(r(ecall)?|(get|fetch)quote)(?: ([\s\S]+))?`
ADMIN ONLY:
 • `rmq(uote)? (\d+)(?:\:(\d+))?`
"""

import html
from random import choice
from asyncio import sleep
from telethon import types


@borg.on(borg.cmd(r"q(uote)?|cite"))
async def add_quote(event):
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


@borg.on(borg.admin_cmd(r"rmq(?:uote)?", r"(\d+)(?:\:(\-?\d+))?"))
async def rm_quote(event):
    match = event.pattern_match
    query_id = match.group(1)
    chat = match.group(2) or str(event.chat_id)
    print(query_id)

    quotes = storage.quotes or None
    try:
        if quotes is not None:
            for q in quotes[chat]:
                if query_id == q["id"]:
                    quotes[chat].remove(q)
                    storage.quotes = quotes
                    await event.reply(f"Quote `{query_id}` in chat: `{chat}` removed")
                    return
    except KeyError:
        pass

    await event.reply(f"No quote with ID `{query_id}`")


@borg.on(borg.cmd(r"(r(ecall)?|(get|fetch)quote)(?: (?P<phrase>[\s\S]+))?"))
async def recall_quote(event):
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
        msg = await event.reply(f"No quotes matching query:  `{phrase}`")
        await sleep(10)
        await msg.delete()
        return

    quote = choice(match_quotes)

    id = quote["id"]
    text = html.escape(quote["text"])
    sender = quote["sender"]
    sender_name = html.escape(f"{sender.first_name} {sender.last_name or ''}")
    msg_date = (quote["date"]).strftime("%B, %Y")

    format_quote = f"<b>{text}</b>"
    format_quote += f"\n<i>- <a href='tg://user?id={sender.id}'>{sender_name}</a>, "
    format_quote += f"<a href='t.me/share/url?url=%2Frecall+{id}'>{msg_date}</a></i>"

    msg = await event.respond(format_quote, parse_mode="html")


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
from asyncio import sleep
from random import choice
from telethon import types
from uniborg.util import cooldown, blacklist


@borg.on(borg.cmd(r"(q(uote)?|cite)"))
@cooldown(15)
async def add_quote(event):
    blacklist = storage.blacklist or set()
    if event.chat_id in blacklist:
        return

    if event.is_private:
        return

    chat = str(event.chat_id)
    if not event.is_reply:
        quotes = storage.quotes or None
        amnt = len(quotes[chat])

        await event.reply(
            f"There are `{amnt}` quotes saved for this group."
            + "\nReply to a message with `/quote` to cite that message, "
            + "and `/recall` to recall.")
        return

    reply_msg = await event.get_reply_message()
    if reply_msg.forward:
        return

    text = reply_msg.raw_text
    if not text:
        return

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
@cooldown(10)
async def recall_quote(event):
    blacklist = storage.blacklist or set()
    if event.chat_id in blacklist:
        return

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
            full_name = f"{first_name} {last_name}"
            username = sender.username.lower()

            if phrase == id:
                match_quotes.append(q)
                break
            if phrase in text:
                match_quotes.append(q)
                continue
            if phrase in full_name:
                match_quotes.append(q)
                continue
            if phrase in username:
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
    msg = await event.respond(format_quote, parse_mode="html")

    await sleep(0.2)

    format_quote += f"\n<i>- <a href='tg://user?id={sender.id}'>{sender_name}</a>, "
    format_quote += f"<a href='t.me/share/url?url=%2Frecall+{id}'>{msg_date}</a></i>"

    await msg.edit(format_quote, parse_mode="html")


@borg.on(borg.blacklist_plugin())
async def on_blacklist(event):
    storage.blacklist = await blacklist(event, storage.blacklist)

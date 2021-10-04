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
from collections import defaultdict
from telethon import types
from uniborg.util import cooldown, blacklist


# Convert from old list format to defaultdict
quotes = defaultdict(dict, storage.quotes or {})
for chat_id, quote_list in quotes.items():
    if isinstance(quote_list, dict):
        continue
    quotes[chat_id] = {
        quote["id"]: {
            k: v for k, v in quote.items() if k != "id"
        } for quote in quote_list
    }
storage.quotes = quotes


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
        amnt = len(storage.quotes[chat])

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

    quote_id = str(reply_msg.id)
    quote = {
        "text": text,
        "sender": sender,
        "date": reply_msg.date
    }

    quotes = storage.quotes
    if quote_id in quotes[chat]:
        msg = await event.reply("Duplicate quote in database")
        await sleep(10)
        await msg.delete()
        try:
            await event.delete()
        except:
            pass
        return

    quotes[chat][quote_id] = quote
    storage.quotes = quotes

    user = (await event.get_sender()).first_name
    await event.respond(f"Quote saved by {user}!  (ID:  `{reply_msg.id}`)",
                        reply_to=reply_msg)
    try:
        await sleep(10)
        await event.delete()
    except:
        pass



@borg.on(borg.admin_cmd(r"rmq(?:uote)?", r"(\d+)(?:\:(\-?\d+))?"))
@cooldown(5)
async def rm_quote(event):
    match = event.pattern_match
    query_id = match.group(1)
    chat = match.group(2) or str(event.chat_id)

    quotes = storage.quotes

    try:
        del quotes[chat][query_id]
        storage.quotes = quotes
        await event.reply(f"Quote `{query_id}` in chat: `{chat}` removed")
    except KeyError:
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
    quotes = storage.quotes

    if not quotes[chat]:
        return

    if not phrase:
        match_quotes = list(quotes[chat].keys())
    else:
        phrase = phrase.lower()
        for id, q in quotes[chat].items():
            text = q["text"].lower()
            sender = q["sender"]
            first_name = sender.first_name.lower()
            last_name = (sender.last_name or "").lower()
            full_name = f"{first_name} {last_name}"
            username = (sender.username or "").lower()

            if phrase == id:
                match_quotes.append(id)
                break
            if phrase in text:
                match_quotes.append(id)
                continue
            if phrase in full_name:
                match_quotes.append(id)
                continue
            if phrase in username:
                match_quotes.append(id)
                continue

    if not match_quotes:
        msg = await event.reply(f"No quotes matching query:  `{phrase}`")
        await sleep(10)
        await msg.delete()
        await event.delete()
        return

    id = choice(match_quotes)
    quote = quotes[chat][id]
    text = html.escape(quote["text"])
    sender = quote["sender"]
    sender_name = html.escape(f"{sender.first_name} {sender.last_name or ''}")
    msg_date = (quote["date"]).strftime("%B, %Y")

    format_quote = f"<b>{text}</b>"
    msg = await event.respond(format_quote, parse_mode="html")

    await sleep(0.5)

    format_quote += f"\n<i>- <a href='tg://user?id={sender.id}'>{sender_name}</a>, "
    format_quote += f"<a href='t.me/share/url?url=%2Frecall+{id}'>{msg_date}</a></i>"

    await msg.edit(format_quote, parse_mode="html")

    try:
        await sleep(60)
        await event.delete()
    except:
        pass


@borg.on(borg.blacklist_plugin())
async def on_blacklist(event):
    storage.blacklist = await blacklist(event, storage.blacklist)

from collections import defaultdict
import html

from telethon import utils
from telethon.tl import types

def get_who_string(who, rank=None):
    who_string = html.escape(utils.get_display_name(who))
    if rank is not None:
        who_string += f' <i>"{html.escape(rank)}"</i>'
    if isinstance(who, (types.User, types.Channel)) and who.username:
        who_string += f" <i>(@{who.username})</i>"
    who_string += f", <a href='tg://user?id={who.id}'>#{who.id}</a>"
    return who_string

@borg.on(borg.admin_cmd(r"kek"))
async def _(event):
    keks = defaultdict(lambda: 0)
    async for msg in borg.iter_messages(event.chat_id, search="kek"):
        if "kek" not in msg.raw_text.lower():
            continue
        if msg.forward and msg.forward.sender_id != msg.sender_id:
            continue
        keks[msg.sender_id] += 1
    keks = sorted(keks.items(), key=lambda i: i[1], reverse=True)

    chat = await event.get_chat()
    lines = []
    if not isinstance(chat, types.User):
        lines.append(f"<b>Uses of kek in {chat.title}</b>")
    for uid, tally in keks:
        user = await borg.get_entity(uid)
        lines.append(f"{get_who_string(user)}: {tally}")
    await event.edit("\n".join(lines), parse_mode="html")

r"""Link Subreddit

When a user mentions a subreddit, the bot will respond with a link to that page on the subreddit.

For example sending `/r/aww/top` will provide a link to the top of /r/aww

Adding `.np` anywhere in the message will remove the link preview.

pattern:  `(?i)(?:[^/\w]|^|\s)/?(r/\w+)(/(?:top|best|new|hot|rising|gilded|controversial|wiki(?:/\S+)?))?\b`
"""

import re
import requests
from telethon import events
from urllib.parse import urljoin
from uniborg.util import edit_blacklist


# Subreddit
@borg.on(events.NewMessage(pattern=re.compile(
                    r"(?i)(?:^|\s)/?(r/[\w_-]{3,21})(/(?:top|best|new|hot|rising|gilded|controversial|wiki(?:/\S+)?))?\b"
                ).findall))
async def link_subreddit(event):
    blacklist = storage.blacklist or set()
    if event.chat_id in blacklist:
        return

    subreddits = []
    msg = await event.reply("Checking...")
    for s in event.pattern_match:
        subreddit = ("".join(s))[2:]
        subreddit_link = urljoin("https://reddit.com/r/", subreddit)

        res = requests.get(subreddit_link)
        if res.status_code == 404: # don't respond if the subreddit doesn't exist
            continue

        subreddits.append(f"[/r/{subreddit}]({subreddit_link})")

    bullet = "• " if len(subreddits) > 1 else ""
    reply_msg = "\n• ".join(subreddits)
    link_bool = ".np" not in event.raw_text and len(subreddits) < 2

    await msg.edit(bullet + reply_msg, link_preview=link_bool)

@borg.on(borg.admin_cmd(r"(r)?blacklist", r"(?P<shortname>\w+)"))
async def blacklist_caller(event):
    storage.blacklist = await blacklist(event, storage.blacklist)

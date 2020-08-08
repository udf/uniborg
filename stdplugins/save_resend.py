# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from telethon import events, utils
from telethon.tl import types
from telethon.tl.functions.messages import SaveDraftRequest


@borg.on(events.Raw(types=types.UpdateDraftMessage))
async def _(update):
    if isinstance(update.draft, types.DraftMessageEmpty):
        return
    if update.draft.message != '.sr':
        return
    reply_id = update.draft.reply_to_msg_id
    if not reply_id:
        return
    message = await borg.get_messages(
        update.peer,
        ids=reply_id,
    )
    await borg.send_message('me', message)
    await borg(SaveDraftRequest(
        peer=update.peer,
        message='',
        reply_to_msg_id=reply_id
    ))
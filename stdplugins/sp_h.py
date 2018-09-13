import asyncio
from telethon import events
from telethon.tl import types

EPIC_MEME = (
"""
⢠⠤⢠⢄⠠⡤⢀⠤⠀⠀⠀⠀⢀⣔⢔⢔⢕⢔⢕⢔⢐⢀⠀⠀⠀⠀⠀⠀
⠸⠥⠸⠁⠠⠧⠘⠤⠀⠀⠀⣐⢗⢕⢗⢕⢕⢕⢕⢔⢑⢐⢀⠀⠀⠀⠀⠀
⢰⠑⢱⢸⠭⢰⠑⢱⢸⠭⢐⣟⣗⣕⢗⣗⢑⢕⢑⢕⢑⠐⢑⢐⢐⢐⢀⠀
⢨⢄⢨⢨⢩⢌⢠⠬⢨⠉⢐⣟⢗⢕⢑⣿⣷⣕⣑⠕⢑⢐⣗⠐⢐⢐⢐⢐
⠸⠜⠘⠜⠸⠜⠸⠥⠨⢀⢐⢑⢕⢕⢑⢛⣿⣿⣷⣔⣴⡟⠓⠀⢀⢔⢑⠑
⠀⠀⠀⠀⠀⠀⠀⠀⢐⢗⢑⠐⠐⢷⣷⣷⣿⣿⣿⣿⣿⢕⢐⢔⢑⢔⠁⠀
⠀⠀⠀⠀⠀⠀⠀⠰⢗⢕⢗⢕⢕⢔⠙⢟⢿⣕⣷⣟⣗⣔⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠘⢶⠄⠀⠐⠁⠐⠁⠀⠀⢀⣐⣖⢷⣟⣷⣿⣷⣔⣀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⢘⣗⣴⣴⠀⠀⠀⢀⣴⣿⣿⢟⢗⢛⣿⣟⣟⣟⣿⣟⣗⠀
⠀⠀⠀⠀⠀⠀⢐⣿⣿⣿⡇⠀⢐⣿⣿⣟⣗⢐⢐⣔⣿⣗⣷⣟⣿⣟⣿⣗
⠀⠀⠀⠀⠀⠀⢰⣿⣿⣟⣁⢐⢿⣟⣿⣿⣗⠐⢐⣟⣿⣟⣟⣟⣷⣟⣿⣗
⠀⠀⠀⠀⠀⠀⢙⣟⣿⣿⣷⣗⣖⣿⣿⣟⢑⠐⢐⣟⣗⣟⣗⣗⢗⠟⢓⣑
⠀⠀⠀⠀⠀⠀⠐⠑⠛⠛⠛⠑⠓⠙⠛⠓⠁⠐⠐⠛⠓⠛⠓⠓⠑⠒⠓⠛
"""
)

@borg.on(events.NewMessage(pattern=r"^h$"))
async def on_h(event):
    message = await event.reply(
        file=types.InputDocument(421851232546587302, -6059663575626880183))

    async def del_filter(del_event):
        if del_event.chat_id and del_event.chat_id != event.chat_id:
            return False
        return del_event.deleted_id == message.id
    fut = borg.await_event(events.MessageDeleted, del_filter)

    try:
        await asyncio.wait_for(fut, timeout=5)
        await event.reply(EPIC_MEME)
    except asyncio.TimeoutError:
        pass


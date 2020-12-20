"""
Assists with transcription of the @JapaneseSpirit channel

New messages are forwarded to saved messages that when edited are sent to the
transcription channel
"""
import telethon.utils
import telethon.events
from telethon.extensions import html


@borg.on(telethon.events.NewMessage(chats=['@JapaneseSpirit']))
async def on_message(event):
    m = event.message
    text = f'jpt:\n[#{m.id}](https://t.me/JapaneseSpirit/{m.id})'
    await borg.send_message('me', text, file=m.photo)


@borg.on(telethon.events.MessageEdited(chats=borg.uid))
async def on_saved_edited(event):
    message = event.message
    if not message.text.startswith('jpt:'):
        return
    html_text = html.unparse(message.message, message.entities).lstrip('jpt:')
    await borg.send_message(
        '@JapaneseTranscript',
        html_text,
        file=message.media,
        parse_mode='HTML'
    )
    await borg.delete_messages('me', message.id)
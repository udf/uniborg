# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
Translates stuff into English
"""
import asyncio
import html
import io
import mimetypes

from telethon import helpers, types

from google.oauth2 import service_account
from google.cloud import translate_v3 as translate
from google.cloud import texttospeech

from uniborg import util


PREFERRED_LANGUAGE = "en"


mimetypes.add_type('audio/mpeg', '.borg+tts')


try:
    credentials = service_account.Credentials.from_service_account_file(
        "google_cloud_key.json")
except FileNotFoundError:
    logger.warn(
        "Google Cloud API key not found, this plugin will be unavailable."
    )
    raise util.StopImport

tl_client = translate.TranslationServiceAsyncClient(credentials=credentials)
tl_parent = f"projects/{credentials.project_id}"
tts_client = texttospeech.TextToSpeechAsyncClient(credentials=credentials)


tl_langs = {}
async def fetch_supported_languages():
    langs = (await tl_client.get_supported_languages(
        parent=tl_parent,
        display_language_code=PREFERRED_LANGUAGE
    )).languages
    global tl_langs
    tl_langs = { lang.language_code.lower(): lang for lang in langs }
    if tl_langs.get("zh-cn") is None:
        tl_langs["zh-cn"] = tl_langs["zh"]
asyncio.create_task(fetch_supported_languages())


allowed_groups = set((int(x) for x in storage.allowed_groups or []))


@borg.on(borg.admin_cmd(r"tl_allow_group"))
async def _(event):
    allowed_groups.add(event.chat_id)
    storage.allowed_groups = list(allowed_groups)
    await event.respond(f"Added {event.chat_id} to allowed groups")


@borg.on(borg.admin_cmd(r"tl_allowed_groups"))
async def _(event):
    groups = {}
    for group in allowed_groups:
        entity = await borg.get_entity(group)
        groups[group] = entity.title

    groups = [ f"`{k}`: {v}" for k, v in groups.items() ]
    await event.respond("\n".join(groups))


@borg.on(borg.cmd(r"tl", r"(?s)(?:\s+(?P<args>.*))?"))
async def _(event):
    if borg.me.bot and event.chat_id not in allowed_groups:
        return

    source, target = None, None
    text = None
    argtext = False
    if args := event.pattern_match.group("args"):
        args = args.split(":::", 1)
        langs = args[0].split(">>", 1)
        if (s:= langs[0]).lower() in tl_langs:
            source = tl_langs[s].language_code
        if len(langs) > 1 and (t:= langs[1]).lower() in tl_langs:
            target = tl_langs[t].language_code
        if len(args) > 1:
            text = args[1]
        elif source is None and target is None:
            text = args[0]

    if target is None:
        target = PREFERRED_LANGUAGE

    if event.is_reply:
        text = (await event.get_reply_message()).raw_text
    elif text:
        argtext = True
    elif not borg.me.bot:
        text = ''
        started = False
        async for m in borg.iter_messages(event.chat_id):
            if started and m.sender_id == borg.uid:
                break
            if m.sender_id != borg.uid:
                started = True
            if not started or not m.raw_text:
                continue
            if ' ' in m.raw_text:
                text = m.raw_text + '\n' + text
            else:
                text = m.raw_text + ' ' + text
    else:
        return

    translation = (await tl_client.translate_text(
        parent=tl_parent,
        contents=[html.escape(text.strip())],
        source_language_code=source,
        target_language_code=target
    )).translations[0]
    translated = translation.translated_text
    langs = (source or translation.detected_language_code, target)

    source, target = (tl_langs[l.lower()].display_name for l in langs)
    result = f"<b>{source} → {target}:</b>\n{translated}"
    if borg.me.bot:
        action = event.respond
    elif argtext:
        action = event.reply
    else:
        action = event.edit
    await action(result, parse_mode="html")


@borg.on(borg.cmd(r"tts", r"(?s)(?:\s+(?P<args>.*))?"))
async def _(event):
    if borg.me.bot and event.chat_id not in allowed_groups:
        return

    lang = None
    text = None
    if args := event.pattern_match.group("args"):
        args = args.split(":::", 1)
        if args[0].lower() in tl_langs:
            lang = args[0]
        if len(args) > 1:
            text = args[1]
        elif lang is None:
            text = args[0]

    if not borg.me.bot and not text:
        await event.delete()

    if not text and event.is_reply:
        text = (await event.get_reply_message()).raw_text

    if not text:
        return

    # Attempt to detect text language
    if lang is None:
        response = await tl_client.detect_language(
            parent=tl_parent,
            content=text.strip()
        )
        lang = response.languages[0].language_code

    voices = (await tts_client.list_voices(language_code=lang)).voices
    if not voices:
        await event.respond(f"No voices for {tl_langs[lang].display_name}")
        return

    response = await tts_client.synthesize_speech(
        input=texttospeech.SynthesisInput(text=text),
        voice=texttospeech.VoiceSelectionParams(
            language_code=lang,
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
        ),
        audio_config=texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3)
    )

    file = io.BytesIO(response.audio_content)
    file.name = 'a.borg+tts'
    await borg.send_file(
        event.chat_id,
        file,
        reply_to=event.reply_to_msg_id or event.id if not borg.me.bot else None,
        attributes=[types.DocumentAttributeAudio(
            duration=0,
            voice=True
        )]
    )


@borg.on(borg.cmd("langs"))
async def _(event):
    langs = "\n".join([
        "<b>Supported languages:</b>",
        *(f"{l.language_code}: {l.display_name}" for _, l in tl_langs.items())
    ])
    if borg.me.bot:
        action = event.respond
    else:
        action = event.edit
    await action(langs, parse_mode="html")

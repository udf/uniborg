# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
Translates stuff into English
"""
import aiohttp
import asyncio
import html
import io
import math
import mimetypes
import re
import time

from telethon import helpers, types

from google.oauth2 import service_account
from google.cloud import translate_v3 as translate
from google.cloud import texttospeech


mimetypes.add_type('audio/mpeg', '.borg+tts')


LANGUAGES = {
    'af': 'Afrikaans',
    'sq': 'Albanian',
    'am': 'Amharic',
    'ar': 'Arabic',
    'hy': 'Armenian',
    'az': 'Azerbaijani',
    'eu': 'Basque',
    'be': 'Belarusian',
    'bn': 'Bengali',
    'bs': 'Bosnian',
    'bg': 'Bulgarian',
    'ca': 'Catalan',
    'ceb': 'Cebuano',
    'ny': 'Chichewa',
    'zh-cn': 'Chinese (Simplified)',
    'zh-tw': 'Chinese (Traditional)',
    'co': 'Corsican',
    'hr': 'Croatian',
    'cs': 'Czech',
    'da': 'Danish',
    'nl': 'Dutch',
    'en': 'English',
    'eo': 'Esperanto',
    'et': 'Estonian',
    'tl': 'Filipino',
    'fi': 'Finnish',
    'fr': 'French',
    'fy': 'Frisian',
    'gl': 'Galician',
    'ka': 'Georgian',
    'de': 'German',
    'el': 'Greek',
    'gu': 'Gujarati',
    'ht': 'Haitian Creole',
    'ha': 'Hausa',
    'haw': 'Hawaiian',
    'iw': 'Hebrew',
    'hi': 'Hindi',
    'hmn': 'Hmong',
    'hu': 'Hungarian',
    'is': 'Icelandic',
    'ig': 'Igbo',
    'id': 'Indonesian',
    'ga': 'Irish',
    'it': 'Italian',
    'ja': 'Japanese',
    'jw': 'Javanese',
    'kn': 'Kannada',
    'kk': 'Kazakh',
    'km': 'Khmer',
    'rw': 'Kinyarwanda',
    'ko': 'Korean',
    'ku': 'Kurdish (Kurmanji)',
    'ky': 'Kyrgyz',
    'lo': 'Lao',
    'la': 'Latin',
    'lv': 'Latvian',
    'lt': 'Lithuanian',
    'lb': 'Luxembourgish',
    'mk': 'Macedonian',
    'mg': 'Malagasy',
    'ms': 'Malay',
    'ml': 'Malayalam',
    'mt': 'Maltese',
    'mi': 'Maori',
    'mr': 'Marathi',
    'mn': 'Mongolian',
    'my': 'Myanmar (Burmese)',
    'ne': 'Nepali',
    'no': 'Norwegian',
    'or': 'Odia (Oriya)',
    'ps': 'Pashto',
    'fa': 'Persian',
    'pl': 'Polish',
    'pt': 'Portuguese',
    'pa': 'Punjabi',
    'ro': 'Romanian',
    'ru': 'Russian',
    'sm': 'Samoan',
    'gd': 'Scots Gaelic',
    'sr': 'Serbian',
    'st': 'Sesotho',
    'sn': 'Shona',
    'sd': 'Sindhi',
    'si': 'Sinhala',
    'sk': 'Slovak',
    'sl': 'Slovenian',
    'so': 'Somali',
    'es': 'Spanish',
    'su': 'Sundanese',
    'sw': 'Swahili',
    'sv': 'Swedish',
    'tg': 'Tajik',
    'ta': 'Tamil',
    'tt': 'Tatar',
    'te': 'Telugu',
    'th': 'Thai',
    'tr': 'Turkish',
    'tk': 'Turkmen',
    'uk': 'Ukrainian',
    'ur': 'Urdu',
    'ug': 'Uyghur',
    'uz': 'Uzbek',
    'vi': 'Vietnamese',
    'cy': 'Welsh',
    'xh': 'Xhosa',
    'yi': 'Yiddish',
    'yo': 'Yoruba',
    'zu': 'Zulu'
}


credentials = service_account.Credentials.from_service_account_file(
    "google_cloud_key.json")
tl_client = translate.TranslationServiceAsyncClient(credentials=credentials)
tl_parent = f"projects/{credentials.project_id}"
tts_client = texttospeech.TextToSpeechAsyncClient(credentials=credentials)


allowed_groups = set((int(x) for x in storage.allowed_groups or []))


@borg.on(borg.admin_cmd(r"tl_allow_group"))
async def _(event):
    allowed_groups.add(event.chat_id)
    storage.allowed_groups = list(allowed_groups)
    await event.respond(f"Added {event.chat_id} to allowed groups")


@borg.on(borg.cmd(r"tl", r"(?:\s+(?P<args>.*))?"))
async def _(event):
    if borg.me.bot and event.chat_id not in allowed_groups:
        return

    source, target = None, None
    text = None
    argtext = False
    if args := event.pattern_match.group("args"):
        args = args.split(":::", 1)
        langs = args[0].split(">>", 1)
        if (s:= langs[0]).lower() in LANGUAGES:
            source = s
        if len(langs) > 1 and (t:= langs[1]).lower() in LANGUAGES:
            target = t
        if len(args) > 1:
            text = args[1]
        elif source is None and target is None:
            text = args[0]

    if target is None:
        target = "en"

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
        contents=[text.strip()],
        source_language_code=source,
        target_language_code=target
    )).translations[0]
    translated = translation.translated_text
    langs = (translation.detected_language_code, target)

    source, target = (LANGUAGES.get(l.lower(), l.upper()) for l in langs)
    result = f"<b>{source} → {target}:</b>\n{html.escape(translated)}"
    if borg.me.bot:
        action = event.respond
    elif argtext:
        action = event.reply
    else:
        action = event.edit
    await action(result, parse_mode="html")


@borg.on(borg.cmd(r"tts", r"(?:\s+(?P<args>.*))?"))
async def _(event):
    if borg.me.bot and event.chat_id not in allowed_groups:
        return

    lang = None
    text = None
    if args := event.pattern_match.group("args"):
        args = args.split(":::", 1)
        if args[0].lower() in LANGUAGES:
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

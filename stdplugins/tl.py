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

def split_text(text, n=40):
    words = text.split()
    while len(words) > n:
        comma = None
        semicolon = None
        for i in reversed(range(n)):
            if words[i].endswith('.'):
                yield ' '.join(words[:i + 1])
                words = words[i + 1:]
                break
            elif not semicolon and words[i].endswith(';'):
                semicolon = i + 1
            elif not comma and words[i].endswith(','):
                comma = i + 1
        else:
            cut = semicolon or comma or n
            yield ' '.join(words[:cut])
            words = words[cut:]
    if words:
        yield ' '.join(words)


class Translator:
    _TKK_RE = re.compile(r"tkk:'(\d+)\.(\d+)'", re.DOTALL)
    _BASE_URL = 'https://translate.google.com'
    _TRANSLATE_URL = 'https://translate.google.com/translate_a/single'
    _TRANSLATE_TTS_URL = 'https://translate.google.com/translate_tts'
    _HEADERS = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:75.0) Gecko/20100101 Firefox/75.0'
    }

    def __init__(self, target='en', source='auto'):
        self._target = target
        self._source = source
        self._session = aiohttp.ClientSession(headers=self._HEADERS)
        self._tkk = None
        self._tkk_lock = asyncio.Lock()

    async def _fetch_tkk(self):
        async with self._session.get(self._BASE_URL) as resp:
            html = await resp.text()
            return tuple(map(int, self._TKK_RE.search(html).groups()))

    def _need_refresh_tkk(self):
        return (self._tkk is None) or (self._tkk[0] != int(time.time() / 3600))

    def _calc_token(self, text):
        """
        Original code by ultrafunkamsterdam/googletranslate:
        https://github.com/ultrafunkamsterdam/googletranslate/blob/bd3f4d0a1386ffa634c8ebbebb3603279f3ece99/googletranslate/__init__.py#L263

        If this ever breaks, the way it was found was in one of the top-100
        longest lines of `translate_m.js` used by translate.google.com, it
        uses a single-line with all these "magic" values and one can look
        around there and use a debugger to figure out how it works. It's
        a very straight-forward port.
        """
        def xor_rot(a, b):
            size_b = len(b)
            c = 0
            while c < size_b - 2:
                d = b[c + 2]
                d = ord(d[0]) - 87 if 'a' <= d else int(d)
                d = (a % 0x100000000) >> d if '+' == b[c + 1] else a << d
                a = a + d & 4294967295 if '+' == b[c] else a ^ d
                c += 3
            return a

        a = []
        text = helpers.add_surrogate(text)
        for i in text:
            val = ord(i)
            if val < 0x10000:
                a += [val]
            else:
                a += [
                    math.floor((val - 0x10000) / 0x400 + 0xD800),
                    math.floor((val - 0x10000) % 0x400 + 0xDC00),
                ]

        d = self._tkk
        b = d[0]
        e = []
        g = 0
        size = len(text)
        while g < size:
            l = a[g]
            if l < 128:
                e.append(l)
            else:
                if l < 2048:
                    e.append(l >> 6 | 192)
                else:
                    if (
                            (l & 64512) == 55296
                            and g + 1 < size
                            and a[g + 1] & 64512 == 56320
                    ):
                        g += 1
                        l = 65536 + ((l & 1023) << 10) + (a[g] & 1023)
                        e.append(l >> 18 | 240)
                        e.append(l >> 12 & 63 | 128)
                    else:
                        e.append(l >> 12 | 224)
                    e.append(l >> 6 & 63 | 128)
                e.append(l & 63 | 128)
            g += 1
        a = b
        for i, value in enumerate(e):
            a += value
            a = xor_rot(a, '+-a^+6')
        a = xor_rot(a, '+-3^+b+-f')
        a ^= d[1]
        if a < 0:
            a = (a & 2147483647) + 2147483648
        a %= 1000000
        return '{}.{}'.format(a, a ^ b)

    async def translate(self, text, target=None, source=None):
        if self._need_refresh_tkk():
            async with self._tkk_lock:
                self._tkk = await self._fetch_tkk()

        params = [
            ('client', 'webapp'),
            ('sl', source or self._source),
            ('tl', target or self._target),
            ('hl', 'en'),
            *[('dt', x) for x in ['at', 'bd', 'ex', 'ld', 'md', 'qca', 'rw', 'rm', 'sos', 'ss', 't']],
            ('ie', 'UTF-8'),
            ('oe', 'UTF-8'),
            ('otf', 1),
            ('ssel', 0),
            ('tsel', 0),
            ('tk', self._calc_token(text)),
            ('q', text),
        ]

        async with self._session.get(self._TRANSLATE_URL, params=params) as resp:
            data = await resp.json()
            return (data[2], target or self._target), \
                ''.join(part[0] for part in data[0] if part[0] is not None)

    async def tts(self, text, target=None):
        if self._need_refresh_tkk():
            async with self._tkk_lock:
                self._tkk = await self._fetch_tkk()

        parts = list(split_text(text))
        result = b''
        for i, part in enumerate(parts):
            params = [
                ('ie', 'UTF-8'),
                ('q', part),
                ('tl', target or self._target),
                ('total', len(parts)),
                ('idx', i),
                ('textlen', len(helpers.add_surrogate(part))),
                ('tk', self._calc_token(part)),
                ('client', 'webapp'),
                ('prev', 'input'),
            ]

            async with self._session.get(self._TRANSLATE_TTS_URL, params=params) as resp:
                if resp.status == 404:
                    raise ValueError('unknown target language')
                else:
                    result += await resp.read()

        return result

    async def close(self):
        await self._session.close()


translator = Translator()


@borg.on(borg.cmd(r"tl", r"(?:\s+(?P<args>.*))?"))
async def _(event):
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

    langs, translated = await translator.translate(
        text.strip(),
        source=source,
        target=target
    )
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
        (lang, _), _ = await translator.translate(text)

    file = io.BytesIO(await translator.tts(text, target=lang))
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


async def unload():
    await translator.close()

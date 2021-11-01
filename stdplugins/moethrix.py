# i don't know how to spell mithrix
from random import choice
import re

from telethon import events, helpers
from telethon.extensions.html import (
  HTMLToTelegramParser, unparse, _add_surrogate, _del_surrogate
)

# generated with (?m)^[^aioue]([aeiouy]+).
vowels = (
  'eeu', 'uau', 'ayu', 'oya', 'au', 'aua', 'uee', 'oyeu', 'o', 'yae', 'eo',
  'ayi', 'uye', 'oyo', 'ueui', 'aya', 'ayo', 'uea', 'eei', 'ooey', 'ouau',
  'oie', 'ayeu', 'oo', 'ee', 'uey', 'yu', 'aeye', 'uaya', 'aue', 'oyu', 'uay',
  'eyi', 'oy', 'aie', 'ouy', 'yei', 'uyi', 'oia', 'iao', 'uyou', 'ueuei', 'ia',
  'aiu', 'oue', 'e', 'iyea', 'oyi', 'ioe', 'ooe', 'aou', 'yi', 'aia', 'uai',
  'ya', 'oua', 'aio', 'iai', 'ye', 'ouay', 'aea', 'auai', 'ou', 'aai', 'eyo',
  'ueu', 'aa', 'iei', 'uiya', 'iou', 'u', 'ao', 'uoye', 'uaa', 'ieu', 'a',
  'uia', 'oi', 'uo', 'oei', 'ae', 'eau', 'oa', 'uaoa', 'eio', 'uoi', 'oyou',
  'iau', 'ayoe', 'aui', 'ooi', 'uya', 'io', 'ei', 'uu', 'iae', 'i', 'uoyi',
  'ay', 'eoe', 'ouie', 'ayee', 'ua', 'eie', 'ayou', 'uie', 'oe', 'uei', 'yo',
  'iya', 'oeo', 'iu', 'uoy', 'eou', 'uy', 'ey', 'eu', 'ea', 'ii', 'iy', 'aiyua',
  'ayoi', 'oye', 'ui', 'ueue', 'oau', 'eye', 'aoi', 'ooie', 'ai', 'uoya',
  'oui', 'ie', 'aae', 'aye', 'ue', 'oey'
)


class MethrixParser(HTMLToTelegramParser):
  def handle_data(self, text):
    text = re.sub(
      '(?i)(m)([aeiouy])(thrix)',
      lambda m: f'{m.group(1)}{choice(vowels)}{m.group(3)}',
      text
    )
    super().handle_data(text)


# lolnami pls make this a method of HTMLToTelegramParser
def moothrix_parse(html):
  if not html:
    return html, []

  parser = MethrixParser()
  parser.feed(_add_surrogate(html))
  text = helpers.strip_text(parser.text, parser.entities)
  return _del_surrogate(text), parser.entities


@borg.on(events.NewMessage(outgoing=True, pattern=re.compile('(?i)m[aeiou]thrix').search))
async def mothrix(event: events.NewMessage.Event):
  m = event.message
  html = unparse(m.message, m.entities)
  await event.edit(
    html,
    parse_mode=moothrix_parse
  )
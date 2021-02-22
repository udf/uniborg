r"""Convert Currency

Converts two different currencies using the [European Central Bank's exchange rates](https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html).

Example: "GBP to/in USD" (case insensitive).
You can also specify an amount of said currency:
"5 GBP to USD".

List currencies using `/currencies`

patterns:  
`(?i)^(\d{1,9}|\d{1,9}\.\d\d?)? ?([a-z]{3}) (?:to|in) ([a-z]{3})$`

`/currencies`
"""

from telethon import events
from uniborg.util import cooldown, edit_blacklist
from time import time, gmtime, strftime
from currency_converter import CurrencyConverter

c = CurrencyConverter("http://www.ecb.int/stats/eurofxref/eurofxref.zip")
# c.__init__("http://www.ecb.int/stats/eurofxref/eurofxref.zip")
link = "https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html"


def update_currencies():
    last_update = storage.last_update or 0
    current = int(time())

    if current - last_update <= 60 * 60 * 24:
        return

    c.__init__("http://www.ecb.int/stats/eurofxref/eurofxref.zip")
    last_update = current
    storage.last_update = last_update
    storage.update_timestamp = strftime("%Y-%m-%d %X", gmtime(last_update))


# Convert Currency
@borg.on(events.NewMessage(
    pattern=r"(?i)^(\d{1,9}|\d{1,9}[\.,]\d\d?)? ?([a-z]{3}) (?:to|in) ([a-z]{3})$"))
async def currency(event):
    blacklist = storage.blacklist or set()
    if event.chat_id in blacklist:
        return

    update_currencies()
    value = event.pattern_match.group(1)

    if not value:
        value = 1
    value = value.replace(",", ".")

    fromcur = event.pattern_match.group(2).upper()
    tocur = event.pattern_match.group(3).upper()

    if fromcur.upper() not in c.currencies:
        return
    if tocur.upper() not in c.currencies:
        return

    result = round(c.convert(value, fromcur, tocur), 2)
    await event.reply(f"**{value} {fromcur} is:**  `{result} {tocur}`")


@borg.on(borg.cmd(r"currencies$"))
@cooldown(60)
async def list_currencies(event):
    blacklist = storage.blacklist or set()
    if event.chat_id in blacklist:
        return

    update_currencies()

    currency_list = ", ".join(sorted(c.currencies))
    update_timestamp = storage.update_timestamp or "Never"
    text = f"**List of supported currencies:**\n{currency_list} \
            \n\nFor a detailed list of supported currencies [click here.]({link}) \
            \nLast updated:  `{update_timestamp}`"
    await event.reply(text, link_preview=False)


@borg.on(borg.admin_cmd(r"(r)?blacklist", r"(?P<shortname>\w+)"))
async def blacklist_caller(event):
    storage.blacklist = await blacklist(event, storage.blacklist)

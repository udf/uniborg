"""Slaps a user the sender replies to, or if there's no reply the sender gets slapped.
10 second cooldown.

pattern: `pattern=r"/(?:slap|kicc)(@\S+)?$`
"""
from asyncio import sleep
from random import choice
from telethon import events
from uniborg.util import cooldown


slap_list = storage.slap_list or [
    # Minecraft:
    "{slapper} slapped {slapee}!",
    "{slapee} walked into a cactus whilst trying to escape {slapper}.",
    "{slapee} was shot by an arrow.",
    "{slapee} was shot by {slapper}.",
    "{slapee} was roasted by {slapper}.",
    "{slapee} was roasted in dragon breath by {slapper}.",
    "{slapee} drowned by {slapper}.",
    "{slapee} was blown up by {slapper}.",
    "{slapee} fell from a high place.",
    "{slapee} was doomed to fall by {slapper}.",
    "{slapee} was squashed by a falling anvil.",
    "{slapee} was squashed by a falling anvil whilst fighting {slapper}.",
    "{slapee} went up in flames.",
    "{slapee} burned to death.",
    "{slapee} was burnt to a crisp whilst fighting {slapper}.",
    "{slapee} went off with a bang.",
    "{slapee} went off with a bang whilst fighting {slapper}.",
    "{slapee} was slain by {slapper}.",
    "{slapee} was fireballed by {slapper}.",
    "{slapee} was killed by {slapper}.",
    "{slapee} died.",
    "{slapee} fucking died.", # Not Minecraft
    "{slapee} died because of {slapper}.",
    # Pokémon:
    "{slapee} is out of usable Pokémon, {slapee} blacked out!",
    "{slapee} is out of usable Pokémon, {slapee} whited out!",
    "{slapee} lost against {slapper}, {slapee} blacked out!",
    "{slapee} is blasting off again!",
    # Games:
    "{slapee}'s mortality was clarified in a single strike.",
    # Tech:
    "{slapee} experienced a kernel panic.",
    "{slapee} was infected with malware from an email {slapper} sent them.",
    "{slapee} blue screened.",
    "{slapee} was cyberbullied by {slapper}.",
    "{slapper} convinced {slapee} to enter `rm -rf /*`.",
    "{slapper} convinced {slapee} to delete System32.",
    # Memes:
    "{slapee} was rickrolled.",
    "{slapee} is fresh out of lives.",
    "{slapee} shot John Wick's dog.",
    "{slapee} was introduced to actual cannibal Shia Labeouf by {slapper}.",
    "{slapper} built a wall and made {slapee} pay for it.",
    "{slapper} turned {slapee} into emergency food.",
    "{slapper}:  __*slaps*__\n{slapee}: HOW CAN (S)HE SLAP?!",
    "{slapee}: Et tu, {slapper}?",
    # Animemes:
    "{slapper}:  Omae wa mou shindeiru.\n{slapee}:  NANI?!",
    "{slapee} was destroyed by {slapper}'s stand.",
    # Misc
    "{slapee} walked off a ledge.",
    "{slapper} sent {slapee} to swim with the fishes.",
    "{slapee} forgot to breathe at the sight of {slapper}.",
]

if not storage.slap_list:
    storage.slap_list = slap_list


async def random_slap(event, slapper, slapee):
    return choice(slap_list).format(slapper=slapper, slapee=slapee)


@borg.on(borg.admin_cmd(r"aslap ((?:\S+ ?)+)"))
async def add_slap(event):
    new_slap = event.pattern_match.group(1)
    if not "{slapee}" in new_slap:
        msg = await event.reply("Requires a slapee")
        await sleep(5)
        await msg.delete()
        return

    slap_list.append(f"{new_slap}")
    storage.slap_list = slap_list
    await event.reply("Added!")


@borg.on(borg.cmd(r"(?:slap|kicc)$"))
@cooldown(10)
async def slap(event):
    me = await event.client.get_me()
    sender = await event.get_sender()
    if not event.is_reply:
        slapper = me.first_name
        slapee = sender
    else:
        slapper = sender.first_name
        slapee = await (await event.get_reply_message()).get_sender()
    mention_slapee = f"[{slapee.first_name}](tg://user?id={slapee.id})"
    await event.respond(await random_slap(event, slapper, mention_slapee))

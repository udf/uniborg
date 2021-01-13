"""Slaps a user the sender replies to, or if there's no reply the sender gets slapped.
10 second cooldown.

pattern: `pattern=r"/(?:slap|kicc)(@\S+)?$`
"""
from random import choice
from telethon import events
from uniborg.util import cooldown


async def random_slap(event, slapper, slapee):
    slap_list = [
        # Minecraft:
        f"{slapper} slapped {slapee}!",
        f"{slapee} walked into a cactus whilst trying to escape {slapper}.",
        f"{slapee} was shot by an arrow.",
        f"{slapee} was shot by {slapper}.",
        f"{slapee} was roasted by {slapper}.",
        f"{slapee} was roasted in dragon breath by {slapper}.",
        f"{slapee} drowned by {slapper}.",
        f"{slapee} was blown up by {slapper}.",
        f"{slapee} fell from a high place.",
        f"{slapee} was doomed to fall by {slapper}.",
        f"{slapee} was squashed by a falling anvil.",
        f"{slapee} was squashed by a falling anvil whilst fighting {slapper}.",
        f"{slapee} went up in flames.",
        f"{slapee} burned to death.",
        f"{slapee} was burnt to a crisp whilst fighting {slapper}.",
        f"{slapee} went off with a bang.",
        f"{slapee} went off with a bang whilst fighting {slapper}.",
        f"{slapee} was slain by {slapper}.",
        f"{slapee} got finished off by {slapper}.",
        f"{slapee} was fireballed by {slapper}.",
        f"{slapee} was killed by {slapper} using magic.",
        f"{slapee} died.",
        f"{slapee} fucking died.", # Not Minecraft
        f"{slapee} died because of {slapper}.",
        # Pokémon:
        f"{slapee} is out of usable Pokémon, {slapee} blacked out!",
        f"{slapee} is out of usable Pokémon, {slapee} whited out!",
        f"{slapee} lost against {slapper}, {slapee} blacked out!",
        f"{slapee} is blasting off again!",
        # Games:
        f"{slapee}'s mortality was clarified in a single strike.",
        # Tech:
        f"{slapee} experienced a kernel panic.",
        f"{slapee} was infected with malware from an email {slapper} sent them.",
        f"{slapee} blue screened.",
        f"{slapee} was cyberbullied by {slapper}.",
        f"{slapper} convinced {slapee} to enter `rm -rf /*`.",
        f"{slapper} convinced {slapee} to delete System32.",
        # Memes:
        f"{slapee} was rickrolled.",
        f"{slapee} is fresh out of lives.",
        f"{slapee} shot John Wick's dog.",
        f"{slapee} was introduced to actual cannibal Shia Labeouf by {slapper}.",
        f"{slapper} built a wall and made {slapee} pay for it.",
        f"{slapper} turned {slapee} into emergency food.",
        f"{slapper}:  __*slaps*__\n{slapee}: HOW CAN (S)HE SLAP?!",
        f"{slapee}: Et tu, {slapper}?",
        # Animemes:
        f"{slapper}:  Omae wa mou shindeiru.\n{slapee}:  NANI?!",
        f"{slapee} was destroyed by {slapper}'s stand.",
        # Misc
        f"{slapee} walked off a ledge.",
        f"{slapper} sent {slapee} to swim with the fishes.",
        f"{slapee} forgot to breathe at the sight of {slapper}.",
    ]
    return choice(slap_list)


@cooldown(10)
@borg.on(events.NewMessage(pattern=r"/(?:slap|kicc)$"))
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

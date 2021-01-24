"""Automatically kick deleted accounts

Will check active groups/channels periodically for deleted accounts, and then kick them.
"""

from asyncio import sleep
from uniborg.util import cooldown
from telethon import events, sessions, errors, types


async def return_deleted(group_id, deleted_admin, deleted_users=set(), filter=None):
    async for user in borg.iter_participants(group_id, filter=filter):
        if not user.deleted: # if it's not a deleted account; ignore
            continue
        try:
            if user.id in deleted_admin[group_id]: # if the account is known to be an admin; ignore
                continue
        except KeyError:
            pass

        deleted_users.add(user.id)
    return deleted_users


@borg.on(events.NewMessage(func=lambda e: not e.is_private))
@cooldown(60 * 60) # Only activate at minimum once an hour
async def kick_deleted(event):
    group = event.chat_id

    deleted_group_admins = set()
    deleted_admin = storage.deleted_admin or dict()
    kick_counter = storage.kick_counter or "0"
    kicked_users = 0 # the amount of kicked users for stats
    response = list() # a list of error responses to delete later
    has_erred = False


    deleted_users = await return_deleted(group, deleted_admin=deleted_admin) # iterate over group members
    try:
        deleted_users.update(await return_deleted(group, deleted_admin,
                deleted_users, types.ChannelParticipantsKicked)) # iterate over banned users
    except (AttributeError, TypeError):
        pass


    if not deleted_users:
        return


    for user in deleted_users:
        try:
            await borg.kick_participant(group, user)
            kicked_users += 1

        except errors.ChatAdminRequiredError: # if bot doesn't have the right permissions to kick accounts; leave
            response.append(await event.respond(
                "ChatAdminRequiredError:  "
                + "I must have the ban user permission to be able to kick deleted accounts."
                + "Please add me back as an admin."))
            logger.info(f"{event.chat_id}:  Invalid permissions")
            await borg.kick_participant(group, "me")
            break

        except errors.UserAdminInvalidError: # if the deleted account is an admin; save the id and send error
            deleted_group_admins.add(f"{user}") # save id
            if has_erred: # don't send error if this has already happened
                continue
            has_erred = True
            response.append(await event.respond(
                "UserAdminInvalidError:  "
                + "An admin has deleted their account, so I cannot kick it from the group."
                +  "Please remove them manually."))

    if deleted_group_admins:
        try:
            deleted_admin[group].update(deleted_group_admins)
        except KeyError:
            deleted_admin[group] = deleted_group_admins
        storage.deleted_admin = deleted_admin
    if kicked_users >= 0:
        logger.info(f"{event.chat_id}:  Kicked {kicked_users}")

    kick_counter = int(kick_counter)
    storage.kick_counter = str(kick_counter + kicked_users)

    if not response:
        return

    await sleep(60)
    try:
        for m in response:
            await m.delete()
    except errors.ChannelPrivateError:
        return


@borg.on(borg.cmd(r"stat(s|istics)?$"))
async def stats(event):
    if not event.is_private:
        return

    await event.reply(f"I have kicked a total of `{storage.kick_counter}` deleted accounts.")

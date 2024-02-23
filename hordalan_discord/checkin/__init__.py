# This example requires the 'message_content' intent.
import os
import logging
from typing import Optional

import dotenv
import discord
import discord.ext.commands
import yaml
import sqlalchemy
from sqlalchemy.orm import Session

from .db.models import Base, DiscordUser, CheckinState, SentStatusMessages

dotenv.load_dotenv(os.environ.get("DISCORD_BOT_ENV"))

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger("discord")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(
    filename=os.environ.get("DISCORD_BOT_LOGFILE", "discord.log"),
    encoding="utf-8",
    mode="w",
)
handler.setFormatter(
    logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
)
logger.addHandler(handler)


with open(os.environ.get("DISCORD_BOT_CONFIG", "config.yaml"), "r") as fh:
    config = yaml.safe_load(fh)
print(config)


engine = sqlalchemy.create_engine(
    config.get("database") or "sqlite:///checkin.db", echo=True
)

intents = discord.Intents.default()
intents.message_content = True

bot = discord.Bot(intents=intents)


@bot.event
async def on_ready():
    logger.info(f"We have logged in as {bot.user}")


async def generate_checkin_status_response(
    ctx: discord.commands.context.ApplicationContext, extra=""
):
    users_in = []
    users_out = []
    with Session(engine) as session:
        for user in session.query(DiscordUser).all():
            if user.checkin.is_in:
                users_in.append(f"<@{user.discord_id}>")
            elif user.checkin.message:
                users_out.append(f"- <@{user.discord_id}>: *{user.checkin.message}*")
            else:
                users_out.append(f"- <@{user.discord_id}>")

    inlist = ", ".join(users_in)
    outlist = "\n".join(users_out)

    msg: discord.Interaction = await ctx.respond("...")
    await msg.edit_original_response(
        content=f"**In:** {inlist}\n**Out:**\n{outlist}\n{extra}"
    )

    with Session(engine) as session:
        for sent_message in (
            session.query(SentStatusMessages)
            .filter(SentStatusMessages.channel == msg.channel_id)
            .all()
        ):
            m = bot.get_message(sent_message.message)
            if m is not None:
                await m.delete()
            session.delete(sent_message)

        sent_message = SentStatusMessages(channel=msg.channel_id, message=msg.id)

        session.add_all([sent_message])
        session.commit()


@bot.slash_command(
    description="Mark yourself as on the LAN right now.",
    guild_ids=config.get("discord_server_ids", []),
)
async def checkin(ctx: discord.commands.context.ApplicationContext):
    print(
        ctx.user.id,  # numeric ID
        ctx.user.name,  # Discord username
        ctx.user.display_name,  # Display name
    )

    with Session(engine) as session:

        user: Optional[DiscordUser] = (
            session.query(DiscordUser).filter_by(discord_id=ctx.user.id).one_or_none()
        )

        if user is None:
            logger.info(f"Creating new user for {ctx.user.name}")
            checkin = CheckinState(is_in=True, message=None)
            user = DiscordUser(
                discord_id=ctx.user.id,
                name=ctx.user.name,
                display_name=ctx.user.display_name,
                checkin=checkin,
            )
            session.add_all([checkin, user])
            session.commit()

        user.checkin.is_in = True
        user.checkin.message = None
        session.commit()

    await generate_checkin_status_response(
        ctx, f"\n***{ctx.user.display_name} checked in.***"
    )


@bot.slash_command(
    description="Mark yourself as away from the LAN.",
    guild_ids=config.get("discord_server_ids", []),
)
@discord.option(
    "message",
    str,
    description="Message (why are you away/when are you back?)",
    default=None,
)
async def checkout(
    ctx: discord.commands.context.ApplicationContext,
    message: Optional[str],
):
    if message is None:
        reply = f"\n***{ctx.user.display_name} checked out.***"
    else:
        reply = f"\n***{ctx.user.display_name} checked out:***\n> {message!s}"

    with Session(engine) as session:

        user = (
            session.query(DiscordUser).filter_by(discord_id=ctx.user.id).one_or_none()
        )

        if user is None:
            logger.info(f"Creating new user for {ctx.user.name}")
            checkin = CheckinState(is_in=False, message=message)
            user = DiscordUser(
                discord_id=ctx.user.id,
                name=ctx.user.name,
                display_name=ctx.user.display_name,
                checkin=checkin,
            )
            session.add_all([checkin, user])
            session.commit()

        user.checkin.is_in = False
        user.checkin.message = message
        session.commit()

    await generate_checkin_status_response(ctx, reply)


@bot.slash_command(
    description="List current status",
    guild_ids=config.get("discord_server_ids", []),
)
async def checkinstatus(ctx: discord.commands.context.ApplicationContext):
    await generate_checkin_status_response(ctx)


def main():
    Base.metadata.create_all(engine)
    bot.run(os.environ.get("DISCORD_TOKEN"))

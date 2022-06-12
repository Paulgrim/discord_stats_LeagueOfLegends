import discord
from datetime import timedelta


def get_champion_image(champion: str):
    """
    generate the link to download the image of a champion
    :param champion:
    :return: link to the image
    """
    return f"https://ddragon.leagueoflegends.com/cdn/12.5.1/img/champion/{champion}.png"


def convert_minute(seconde: str):
    duration = str(timedelta(seconds=int(seconde)))
    if duration[0:2] == "0:":
        duration = duration[2:]
    return duration


def embed_match_stat(stats: dict):
    """
    not used here, but it can give you some idea to improve stats presentation
    :param stats:
    :return:
    """
    embed = discord.Embed(
        title=stats['name'],
        colour=discord.Colour(0x532020))
    embed.add_field(name=stats['gameMode'], value=stats['champion'], inline=True)
    embed.add_field(name="WIN" if stats['win'] else "LOSE", value=stats['role'], inline=True)
    embed.add_field(name="K/D/A", value=f"{stats['kill']}/{stats['death']}/{stats['assists']}", inline=True)
    embed.add_field(name="CS", value=stats['cs'], inline=True)
    embed.add_field(name="Damage", value=stats['damage'], inline=True)
    embed.add_field(name="Gold per minute", value="{:10.0f}".format(stats['goldMinute']))
    embed.add_field(name="Game duration", value=convert_minute(stats['duration']), inline=True)
    embed.set_image(url=get_champion_image(stats['champion']))
    return embed


def embed_help(prefix):
    """
    embedding for the help command
    :param prefix:
    :return:
    """
    embed = discord.Embed(
        title="HELP",
        colour=discord.Colour(0x532020))
    embed.set_image(url=get_champion_image("Yuumi"))
    embed.add_field(name=f"{prefix}add", value="Add a player, please attach all letters ", inline=False)
    embed.add_field(name=f"{prefix}del", value="Remove a player, please attach all letters ", inline=False)
    embed.add_field(name=f"{prefix}gamesday", value="Games of the day, you can specify how many games you want",
                    inline=False)
    embed.add_field(name=f"{prefix}rank", value="Get the rank of all players", inline=False)
    embed.add_field(name=f"{prefix}stats",
                    value="Get stats, you can specify how many games to take into account (0 <= <= 20)", inline=False)
    embed.add_field(name=f"{prefix}players", value="Players in the list", inline=False)
    return embed

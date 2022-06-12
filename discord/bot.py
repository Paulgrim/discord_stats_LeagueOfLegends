# -*- coding: utf-8 -*-

from tabulate import tabulate
from request_lol import *
from embedding import embed_help, convert_minute
from discord.ext import commands, tasks
from datetime import datetime

load_dotenv()
api_key = os.environ.get('BOT_KEY')

# convert rank to emoji
rank_to_emoji = {
    "IRON": "🧲",
    "BRONZE": "🥉",
    "SILVER": "🥈",
    "GOLD": "🥇",
    "DIAMOND": "💎",
    "MASTER": ":man_teacher_tone1:",
    "GRANDMASTER": "👑",
    "CHALLENGER": "🌕",
}

# convert rank to integer
rank_ordered = {
    "IRON": 0,
    "BRONZE": 1,
    "SILVER": 2,
    "GOLD": 3,
    "DIAMOND": 4,
    "MASTER": 5,
    "GRANDMASTER": 6,
    "CHALLENGER": 7,
}

# convert roman number to float (to sort players)
roman_numeral = {
    'IV': 0.1,
    'III': 0.2,
    'II': 0.3,
    'I': 0.4
}

prefix = "!"


class DiscordBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=prefix)
        # commands
        self.add_command(commands.Command(self.rank, name="rank"))
        self.add_command(commands.Command(self.gamesday, name="gamesday"))
        self.add_command(commands.Command(self.stats, name="stats"))
        self.add_command(commands.Command(self.add_player, name="add"))
        self.add_command(commands.Command(self.delete_player, name="del"))
        self.add_command(commands.Command(self.list_player, name="players"))

        self.remove_command('help')
        self.add_command(commands.Command(self.help, name="help"))

    @staticmethod
    async def on_ready():
        print('Bot is ready!')

    async def on_raw_reaction_add(self, payload):
        """
        Doesnt use here. Detect when someone react to a message
        https://discordpy.readthedocs.io/en/stable/api.html?highlight=on_raw_reaction_add#discord.on_raw_reaction_add
        :param payload: RawReactionActionEvent
        :return:
        """
        # Detect bot reaction
        if self.get_user(payload.user_id) == self.user:
            return

    async def rank(self, ctx):
        """
        Commands to show ranks
        :param ctx: iscord.ext.commands.Context
        :return:
        """
        msg = "**RANK** \n"
        rank = dict()
        sort_id = dict()
        pseudo = list()
        LP = list()
        rank_name = list()
        winLoss = list()
        for id in list_id:
            stat = get_rank(id)
            if stat['success']:
                sort_id[stat['name']] = rank_ordered[stat['tier']] + roman_numeral[stat['rank']]
                rank[stat['name']] = {
                    'rank_name': f"{rank_to_emoji[stat['tier']]}{'S' if stat['queue'] == 'RANKED_SOLO_5x5' else 'F'} {stat['tier']:<8} {stat['rank']:<3}",
                    'WL': f"{stat['win']}/{stat['losses']}",
                    'LP': f"{stat['LP']}"
                }
        for name, _ in sorted(sort_id.items(), key=lambda item: item[1], reverse=True):
            pseudo.append(name)
            LP.append(rank[name]['LP'])
            rank_name.append(rank[name]['rank_name'])
            winLoss.append(rank[name]['WL'])
        data = {
            ' ': pseudo,
            'Rank': rank_name,
            'W/L': winLoss,
            'LP': LP
        }
        msg += f'```{tabulate(data, headers="keys", tablefmt="github")}```'
        await ctx.send(msg)

    async def gamesday(self, ctx, *args):
        """
        Commands to show all matchs of the day
        can get the last x match by adding an args
        :param ctx: discord.ext.commands.Context
        :param args:
        :return:
        """
        time_message = ctx.message.created_at
        count = 40
        if len(args) > 0 and args[0].isnumeric():
            tmp_count = int(args[0])
            if tmp_count < 10:
                count = tmp_count
        # stats run 10:00 to 10:00 then next day
        if time_message.hour < 10:
            startTime = (time_message - datetime.timedelta(days=1)).replace(hour=10, minute=0, second=0,
                                                                            microsecond=0)
        else:
            startTime = time_message.replace(hour=10, minute=0, second=0, microsecond=0)
            start_timestamp = int(startTime.timestamp())
        msg = f"Since {startTime.strftime('%d/%m/%Y %H:%M')}"
        missing = ""
        data = dict()
        data["name"] = list()
        data['champion'] = list()
        data['WIN'] = list()
        data['cs'] = list()
        data['damage'] = list()
        data['gameMode'] = list()
        data['kda'] = list()
        data['gpm'] = list()
        data['gameDuration'] = list()
        data['role'] = list()
        data['wModeRole'] = list()
        data['damageCsGpm'] = list()
        cpt = 0
        for id in list_id:
            try:
                list_match = get_list_match(id, startTime=start_timestamp, count=count)
                for match in list_match:
                    stats = get_stats_match(get_match_stat(match), id)
                    if stats["gameMode"] != 'ARAM':
                        data["name"].append(stats['name'])
                        data['champion'].append(stats['champion'])
                        data['kda'].append(f"{stats['kill']}/{stats['death']}/{stats['assists']}")
                        gpm = "{:.0f}".format(stats['goldMinute'])
                        duration = convert_minute(stats['duration'])
                        win = f'{"✅" if stats["win"] else "🤡"}'
                        info = "{:<1}{:<8}{:<8}".format(win, stats["gameMode"], stats["role"])
                        data['wModeRole'].append(info)
                        data['damageCsGpm'].append(
                            "{:<6}{:<4}{:<4}{:<6}".format(stats['damage'], stats['cs'], gpm, duration))
                        cpt += 1
            except Exception as e:
                print(e)
                missing += f"{id}, "
        if len(missing) != 0:
            missing = missing[:-2]
            missing += " ➡ no game played"
        if cpt > 0:
            embedding = tabulate({
                ' ': data["name"],
                'Champ': data['champion'],
                'Win Mode Role': data['wModeRole'],
                'K/D/A': data['kda'],
                'Damage CS G/min Dur': data['damageCsGpm'],
            },
                headers='keys',
                tablefmt='github')
            msg += "\n ```" + embedding + "```"
        result = msg + '\n' + missing
        await ctx.send(result)

    async def stats(self, ctx, *args):
        """
        Commands to show stats of all ids of the day
        or we can precise a number 0<= <= 100 to have the number of last game desired

        :param ctx: discord.ext.commands.Context
        :param args:
        :return:
        """
        time_message = ctx.message.created_at
        count = 40
        # stats run 10:00 to 10:00 then next day
        try:
            if len(args) > 0:
                stats = ""
                start_timestamp = None
                arg_count = int(args[0])
                if arg_count <= 20 and arg_count >= 0:
                    count = arg_count
            else:
                if time_message.hour < 10:
                    startTime = (time_message - datetime.timedelta(days=1)).replace(hour=10, minute=0, second=0,
                                                                                    microsecond=0)
                else:
                    startTime = time_message.replace(hour=10, minute=0, second=0, microsecond=0)
                    start_timestamp = int(startTime.timestamp())
                stats = f"Since {startTime.strftime('%d/%m/%Y %H:%M')}"
            missing = ""
            pseudo = list()
            winLoss = list()
            ratio = list()
            cpt = 0
            match = dict()
            for id in list_id:
                if start_timestamp is None:
                    match[id] = get_list_match(id, count=count)
                else:
                    match[id] = get_list_match(id, startTime=start_timestamp, count=count)
            for id in list_id:
                win, loss = count_win(match[id], id)
                if win + loss == 0:
                    missing += f"{id}, "
                else:
                    pseudo.append(id)
                    winLoss.append(f"{win}/{loss}")
                    if loss != 0:
                        ratio.append("{:.2f}".format(win / loss))
                    else:
                        ratio.append(f"{win}")
                cpt += 1
            if len(missing) != 0:
                missing = missing[:-2]
                missing += " ➡ no game played"
            if cpt > 0:
                stats += f"\n ```{tabulate({' ': pseudo, 'W/L': winLoss, 'Ratio': ratio}, headers='keys', tablefmt='github')}```"
            result = stats + '\n' + missing
        except Exception as e:
            print(e)

            result = f"Error : {prefix}stats and option are 'all' and the number of game desired (0<= <=100)\n" \
                     f"```{prefix}stats 10 | => 10 last games between 0 and 100\n" \
                     f"{prefix}stats    | stats of the day```"
        await ctx.send(result)

    async def add_player(self, ctx, *args):
        """
        Add players to the list_id
        :param ctx: discord.ext.commands.Context
        :param args:
        :return:
        """
        pseudo = list()
        notFound = list()
        for arg in args:
            try:
                r = get_summoner_v4(arg)
                pseudo.append(r['name'])
            except:
                notFound.append(arg)
        # check if pseudo is already in the file
        for id in pseudo:
            if id in list_id:
                pseudo.remove(id)
        # add the pseudo in the file
        if len(pseudo) > 0:
            list_id.extend(pseudo)
        with open('players.json', 'w') as file:
            file.write(json.dumps({'list_id': list_id}))
        msg = ""
        if len(pseudo) > 0:
            for name in pseudo:
                msg += f"{name} "
            msg += "added.\n"
        else:
            msg += "No player has been added.\n"
        if len(notFound) > 0:
            for name in notFound:
                msg += f"{name} "
            msg += "not found."
        await ctx.send(msg)

    async def delete_player(self, ctx, *args):
        """
        Delete player from the list id
        :param ctx: discord.ext.commands.Context
        :param args:
        :return:
        """
        pseudo = list()
        notFound = list()
        for arg in args:
            try:
                r = get_summoner_v4(arg)
                pseudo.append(r['name'])
            except:
                notFound.append(arg)
        # check if pseudo is the list id
        for id in pseudo:
            if id not in list_id:
                pseudo.remove(id)
        # delete pseudo in the file
        if len(pseudo) > 0:
            for name in pseudo:
                list_id.remove(name)
        with open('players.json', 'w') as file:
            file.write(json.dumps({'list_id': list_id}))
        msg = ""
        if len(pseudo) > 0:
            for name in pseudo:
                msg += f"{name} "
            msg += "removed.\n"
        else:
            msg += "No player has been removed.\n"
        if len(notFound) > 0:
            for name in notFound:
                msg += f"{name} "
            msg += "not found."
        await ctx.send(msg)

    async def list_player(self, ctx):
        """
        Send all the players in the list
        :param ctx:
        :return:
        """
        msg = "In the list : "
        for name in list_id:
            msg += f"{name}, "
        await ctx.send(msg)

    async def help(self, ctx):
        """
        the command help
        :param ctx: discord.ext.commands.Context
        :return:
        """
        embed = embed_help(prefix)
        await ctx.send(embed=embed)


if __name__ == '__main__':
    bot = DiscordBot()
    bot.run(api_key)

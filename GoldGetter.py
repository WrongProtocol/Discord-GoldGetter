import discord
import requests
import os
from discord.ext import commands
from dotenv import load_dotenv

# Load the environment variables from a .env file
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# Set up intents for the bot
intents = discord.Intents.default()
intents.message_content = True

# Set up the bot
bot = commands.Bot(command_prefix='!', intents=intents)
titleText = "Carmine's Gold Getter with data from Summit Metals\n"

# Function to get the gold price
def get_gold_price():
    url = os.getenv('GOLD_LOOKUP_URL')
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        gold_bid = data.get("goldBid")
        gold_change = data.get("goldChange")
        gold_change_percent = data.get("goldChangePercent")

        if gold_bid is not None and gold_change is not None and gold_change_percent is not None:
            return {
                "gold_bid": gold_bid,
                "gold_change": gold_change,
                "gold_change_percent": gold_change_percent
            }
        else:
            return None

    except requests.RequestException as e:
        return {"error": str(e)}

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

@bot.command(name='gold', help='Get the current gold spot price. With the optional arguments, this function can be used as a spot calculator.  For example, !gold 1350 .5 would tell you the premium of a 1/2 oz compared to current spot price.')
async def gold(ctx, param1: float = commands.parameter(default=None, description="The price you're checking"), param2: float = commands.parameter(default=None, description="The weight you're checking in decimal format. ex: 1/10th would be .1")):

# if BOTH parameters are present, then we function as a spot calculator
    if param1 is not None and param2 is not None:
        gPriceQuery = param1
        gWeight = param2
        price_data = get_gold_price()
        gBid = round(price_data['gold_bid'], 2)

        # get the difference in price between the query price and spot price
        gWeightedPrice = round(gBid * gWeight, 2)
        gPriceDiff = round(gPriceQuery - gWeightedPrice, 2)
        gPercentOver = round((gPriceDiff / gWeightedPrice) * 100, 2)
        aboveOrBelow = "above" if gPriceDiff >= 0 else "BELOW"
        overOrUnder = "over" if gPriceDiff >= 0 else "UNDER"

        # after the above/below,over/under switches are set, normalize the price diff
        gPriceDiff = abs(gPriceDiff)
        gPercentOver = abs(gPercentOver)


        await ctx.send(f'{titleText}'
                       f'**{param2}oz** @ **${param1}** '
                       f'is **${gPriceDiff} {aboveOrBelow}** the spot of ${gWeightedPrice} for {gWeight}oz\n'
                       f'**{gPercentOver}% {overOrUnder}**')
        
# if NO parameters are present, we just fetch the current spot price. 
    else:
        price_data = get_gold_price()
        gBid = round(price_data['gold_bid'], 2)
        gChange = round(price_data['gold_change'], 2)


        if price_data is None:
            await ctx.send("Could not retrieve all required gold price information. Please try again later.")
        
        elif "error" in price_data:
            await ctx.send(f"Error fetching gold price: {price_data['error']}")
        
        else:
            await ctx.send(f'{titleText}'
                f"Gold Bid: ${gBid}\n"
                f"Gold Change: ${gChange}\n"
                f"Gold Change Percent: {price_data['gold_change_percent']}%"
            )

bot.run(DISCORD_TOKEN)

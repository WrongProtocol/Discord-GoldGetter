import discord
import requests
import os
from discord.ext import commands
from dotenv import load_dotenv

# Load the environment variables from a .env file
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GOLD_LOOKUP_URL = os.getenv('GOLD_LOOKUP_URL')

# Set up intents for the bot
intents = discord.Intents.default()
intents.message_content = True

# Set up the bot
bot = commands.Bot(command_prefix='!', intents=intents)
TITLE_TEXT = "Carmine's Gold Getter with data from Summit Metals\n"

# Function to get the gold price
def get_gold_price():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }

    try:
        response = requests.get(GOLD_LOOKUP_URL, headers=headers)
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

# Function to calculate spot price difference
def calculate_spot_difference(price_query, weight, gold_bid):
    weighted_price = round(gold_bid * weight, 2)
    price_diff = round(price_query - weighted_price, 2)
    percent_over = round((price_diff / weighted_price) * 100, 2)
    above_or_below = "above" if price_diff >= 0 else "BELOW"
    over_or_under = "over" if price_diff >= 0 else "UNDER"

    # Normalize the price diff and percentage
    price_diff = abs(price_diff)
    percent_over = abs(percent_over)

    return {
        "weighted_price": weighted_price,
        "price_diff": price_diff,
        "percent_over": percent_over,
        "above_or_below": above_or_below,
        "over_or_under": over_or_under
    }

# Function to send spot price information
def format_spot_price_message(price_data):
    gBid = round(price_data['gold_bid'], 2)
    gChange = round(price_data['gold_change'], 2)
    return (
        f"{TITLE_TEXT}"
        f"Gold Bid: ${gBid}\n"
        f"Gold Change: ${gChange}\n"
        f"Gold Change Percent: {price_data['gold_change_percent']}%"
    )

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

@bot.command(name='gold', help='Get the current gold spot price. With the optional arguments, this function can be used as a spot calculator.  For example, !gold 1350 .5 would tell you the premium of a 1/2 oz compared to current spot price.')
async def gold(ctx, param1: float = commands.parameter(default=None, description="The price you're checking"), param2: float = commands.parameter(default=None, description="The weight you're checking in decimal format. ex: 1/10th would be .1")):
    price_data = get_gold_price()

    if price_data is None:
        await ctx.send("Could not retrieve all required gold price information. Please try again later.")
        return
    elif "error" in price_data:
        await ctx.send(f"Error fetching gold price: {price_data['error']}")
        return

    # If both parameters are present, calculate the spot difference
    if param1 is not None and param2 is not None:
        result = calculate_spot_difference(param1, param2, price_data['gold_bid'])
        await ctx.send(
            f'{TITLE_TEXT}'
            f'**{param2}oz** @ **${param1}** '
            f'is **${result["price_diff"]} {result["above_or_below"]}** the spot of ${result["weighted_price"]} for {param2}oz\n'
            f'**{result["percent_over"]}% {result["over_or_under"]}**'
        )
    else:
        # If no parameters are provided, just send the current spot price
        await ctx.send(format_spot_price_message(price_data))

bot.run(DISCORD_TOKEN)

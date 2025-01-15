import discord
import requests
import os
from discord.ext import commands
from dotenv import load_dotenv

# Load the environment variables from a .env file
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GOLD_LOOKUP_URL = os.getenv('GOLD_LOOKUP_URL')
EXCHANGE_RATE_API_URL = "https://free.ratesdb.com/v1/rates?from=USD&to={}" # URL for currency conversion

# Set up intents for the bot
intents = discord.Intents.default()
intents.message_content = True

# Set up the bot with a command prefix of '!' and specify the intents
bot = commands.Bot(command_prefix='!', intents=intents)
SUB_TEXT = "*data from Summit Metals*\n"

# Function to get the gold price
def get_metal_prices():
    # Set headers to mimic a browser request to avoid getting blocked
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }

    try:
        # Send a GET request to the gold price lookup URL
        response = requests.get(GOLD_LOOKUP_URL, headers=headers)
        response.raise_for_status()  # Raise an error if the response status is not 200 (OK)
        data = response.json()

        # Extract necessary gold price data from the response
        gold_ask = data.get("goldAsk")
        gold_change = data.get("goldChange")
        gold_change_percent = data.get("goldChangePercent")
        silver_ask = data.get("silverAsk")
        silver_change = data.get("silverChange")
        silver_change_percent = data.get("silverChangePercent")
        platinum_ask = data.get("platinumAsk")
        platinum_change = data.get("platinumChange")
        platinum_change_percent = data.get("platinumChangePercent")
        # Return the gold price data if all values are present
        # note we assume that if we got a gold_ask, we'll have the rest of the parameters as well, though
        # this could be a false presumpion in the case that the API changes.
        if gold_ask is not None :
            return {
                "gold_ask": gold_ask,
                "gold_change": gold_change,
                "gold_change_percent": gold_change_percent,
                "silver_ask": silver_ask,
                "silver_change": silver_change,
                "silver_change_percent": silver_change_percent,
                "platinum_ask": platinum_ask,
                "platinum_change": platinum_change,
                "platinum_change_percent": platinum_change_percent
            }
        else:
            return None

    except requests.RequestException as e:
        # Return an error message if there is an issue with the request
        return {"error": str(e)}

# Python does this crazy thing where decimals like .5 fails the .isnumeric() test. 
# instead, we have to use this function to test it out......
def is_float(string):
    try:
        float(string)  # Try converting the string to a float
        return True
    except ValueError:
        return False
    
# Function to get the exchange rate for the specified currency
def get_exchange_rate(to_currency):
    try:
        response = requests.get(EXCHANGE_RATE_API_URL.format(to_currency))
        response.raise_for_status()  # Raise an error if the response status is not 200 (OK)
        data = response.json()
        rate = data.get("data").get("rates").get(to_currency)
        if rate is not None:
            return rate
        else:
            return None
    except requests.RequestException as e:
        print(e)
        return None

# Function to calculate spot price difference
def calculate_spot_difference(price_query, weight, gold_ask):
    # Calculate the weighted price based on gold ask and weight provided by user
    weighted_price = round(gold_ask * weight, 2)
    # Calculate the difference between user's price and the weighted spot price
    price_diff = round(price_query - weighted_price, 2)
    # Calculate the percentage over or under the spot price
    percent_over = round((price_diff / weighted_price) * 100, 2)
    # Determine if the user's price is above or below the spot price
    above_or_below = "above" if price_diff >= 0 else "BELOW"
    over_or_under = "over" if price_diff >= 0 else "UNDER"

    # Normalize the price diff and percentage (always positive for easier understanding)
    price_diff = abs(price_diff)
    percent_over = abs(percent_over)

    # Return the calculated values
    return {
        "weighted_price": weighted_price,
        "price_diff": price_diff,
        "percent_over": percent_over,
        "above_or_below": above_or_below,
        "over_or_under": over_or_under
    }

# Function to format the spot price information for sending to the user
def format_spot_price_message(price_data, currency_code="USD"):
    # Get the conversion rate if a currency other than USD is specified
    rate = 1 if currency_code == "USD" else get_exchange_rate(currency_code)
    if rate is None:
        return f"Error: Could not retrieve exchange rate for {currency_code}."

    # Convert the gold price to the specified currency
    gAsk = round(price_data['gold_ask'] * rate, 2)
    gChange = round(price_data['gold_change'] * rate, 2)
    # Return a formatted string with the gold price details in the specified currency
    return (
        f"Gold Ask: {gAsk} {currency_code}\n"
        f"Gold Change: {gChange} {currency_code}\n"
    #    f"Gold Change Percent (%usd): {price_data['gold_change_percent']}%\n"
        f"{SUB_TEXT}"
    )

@bot.event
async def on_ready():
    # Notify when the bot has connected to Discord
    print(f'{bot.user.name} has connected to Discord!',  flush=True)

@bot.command(name='spot', help='use !gold at this time')
async def spot(ctx):
    # Retrieve the current gold price data
    price_data = get_metal_prices()
    gAsk = round(price_data['gold_ask'], 2)
    gChange = round(price_data['gold_change'], 2)
    sAsk = round(price_data['silver_ask'], 2)
    sChange = round(price_data['silver_change'], 2)
    pAsk = round(price_data['platinum_ask'], 2)
    pChange = round(price_data['platinum_change'], 2)
    await ctx.send(
                   f'Gold: **{gAsk}** USD\n'
                   f'Gold Change: {gChange} \n'
                   f'Silver: **{sAsk}** USD\n'
                   f'Silver Change: {sChange}\n'
                   f'Platinum: **{pAsk}** USD\n'
                   f'Platinum Change: {pChange}\n'
                   'Use **!gold** to perform more gold-specific lookups such as fractional and premium calculations. !help gold for more information.\n'
                   f"{SUB_TEXT}")

@bot.command(name='gold', help='!gold gets spot price. !gold .5 would tell you the spot price for a half oz.  !gold 1350 .5 would calculate how much over/under that price is for .5oz. You can also specify a currency as the last parameter of any of these commands, e.g. !gold CAD,   !gold .5 CAD    or  !gold 2000 .5 CAD')
async def gold(ctx, 
               param1: str = commands.parameter(default=None, description=""), #param1 is listed as a str because of the use case of !gold CAD which we have to check for
               param2: str = commands.parameter(default=None, description=""), #param2 is listed as a STR because it could also be used as a currency in the example of !gold .1 USD
               param3: str = commands.parameter(default="USD", description="")):

# TODO THIS FUNCTION STARTED OUT SO SIMPLE, BUT FEATURE-CREEP TURNED IT MESSY. REWRITE HOW ALL THE PARAMETERS ARE HANDLED
# OR BREAK THIS OUT INTO A FEW DIFFERENT COMMANDS. 

    # print out the request for debug purposes
    print("p1 ", param1, ", p2 ", param2, ", p3 ", param3,  flush=True)

    # Retrieve the current gold price data
    price_data = get_metal_prices()

    # Handle errors or missing data
    if price_data is None:
        await ctx.send("Could not retrieve all required gold price information. Please try again later.")
        return
    elif "error" in price_data:
        await ctx.send(f"Error fetching gold price: {price_data['error']}")
        return

    
    currency_code = param3.upper()

    # there is a use case where the person just writes "!gold CAD" to retrieve spot prices in another currency
    # therefore, were have to check if the first param is alphabetic. If so, we will set currencycode to param1
    # so that it can be used later in the "else" case where format_spot_price_message is called
    if param1 is not None and param1.isalpha():
        currency_code = param1

    # there is a case where someone writes something like "!gold .25" or "!gold .25 CAD"
    # where they want to see the current spot price for that fractional weight. 
    if param1 is not None and is_float(param1) and (param2 is None or (isinstance(param2, str) and not is_float(param2))):

        theweight = float(param1)
        thecurrencycode = param2

        #if param2 is None (no currency defined), use USD
        if thecurrencycode is None: thecurrencycode = "USD"

        # Get the conversion rate for the specified currency
        convRate = 1 if thecurrencycode == "USD" else get_exchange_rate(thecurrencycode)

        # convert to specified currency , and apply fractional weight
        priceout = round((price_data['gold_ask'] * convRate) * theweight, 2)

        await ctx.send(
            f'**{theweight}oz** ask is at **{priceout} {thecurrencycode}**\n'
            f"{SUB_TEXT}"
        )
        return

    # If both parameters (price and weight) are provided and are Not None and are both numeric, then the user wants us to calculate the spot difference
    if ((param1 is not None and 
        (is_float(param1)))
         and (param2 is not None and 
         (is_float(param2)))):

        # Get the conversion rate for the specified currency
        rate = 1 if currency_code == "USD" else get_exchange_rate(currency_code)
        if rate is None:
            await ctx.send(f"Error: Could not retrieve exchange rate for {currency_code}. Please try again later.")
            return
        # Convert the gold ask price to the specified currency
        gold_ask_converted = price_data['gold_ask'] * rate
        result = calculate_spot_difference(float(param1), float(param2), gold_ask_converted)
        await ctx.send(
            f'{param2}oz @ {param1} {currency_code} '
            f'is **{result["price_diff"]} {currency_code} {result["above_or_below"]}** the spot of {result["weighted_price"]} {currency_code} for {param2}oz\n'
            f'**{result["percent_over"]}% {result["over_or_under"]}**\n'
            f"{SUB_TEXT}"
        )
    else:
        # If no parameters are provided, just send the current spot price
        await ctx.send(format_spot_price_message(price_data, currency_code))

# Run the bot with the provided Discord token
bot.run(DISCORD_TOKEN)

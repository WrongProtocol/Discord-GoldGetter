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
TITLE_TEXT = "Carmine's Gold Getter with data from Summit Metals\n"

# Function to get the gold price
def get_gold_price():
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
        gold_bid = data.get("goldBid")
        gold_change = data.get("goldChange")
        gold_change_percent = data.get("goldChangePercent")

        # Return the gold price data if all values are present
        if gold_bid is not None and gold_change is not None and gold_change_percent is not None:
            return {
                "gold_bid": gold_bid,
                "gold_change": gold_change,
                "gold_change_percent": gold_change_percent
            }
        else:
            return None

    except requests.RequestException as e:
        # Return an error message if there is an issue with the request
        return {"error": str(e)}

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
def calculate_spot_difference(price_query, weight, gold_bid):
    # Calculate the weighted price based on gold bid and weight provided by user
    weighted_price = round(gold_bid * weight, 2)
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
    gBid = round(price_data['gold_bid'] * rate, 2)
    gChange = round(price_data['gold_change'] * rate, 2)
    # Return a formatted string with the gold price details in the specified currency
    return (
        f"{TITLE_TEXT}"
        f"Gold Bid: {gBid} {currency_code}\n"
        f"Gold Change: {gChange} {currency_code}\n"
        f"Gold Change Percent: {price_data['gold_change_percent']}%"
    )

@bot.event
async def on_ready():
    # Notify when the bot has connected to Discord
    print(f'{bot.user.name} has connected to Discord!')

@bot.command(name='gold', help='Get the current gold spot price. With the optional arguments, this function can be used to get spot prices in another currency, e.g. !spot CAD.  Also, as a spot calculator.  For example, !gold 1350 .5 would tell you the premium of a 1/2 oz compared to current spot price. You can also specify a currency, e.g. !gold 2000 .5 CAD')
async def gold(ctx, 
               param1: str = commands.parameter(default=None, description="The price you're checking"), #param1 is listed as a str because of the use case of !gold CAD which we have to check for
               param2: float = commands.parameter(default=None, description="The weight you're checking in decimal format. ex: 1/10th would be .1"),
               param3: str = commands.parameter(default="USD", description="The currency code. ex: USD, CAD")):
    # Retrieve the current gold price data
    price_data = get_gold_price()

    # Handle errors or missing data
    if price_data is None:
        await ctx.send("Could not retrieve all required gold price information. Please try again later.")
        return
    elif "error" in price_data:
        await ctx.send(f"Error fetching gold price: {price_data['error']}")
        return

    
    currency_code = param3.upper()

    # there is a use case where the person just writes !gold CAD to retrieve spot prices in another currency
    # therefore, were have to check if the first param is alphabetic. If so, we will set currencycode to param1
    # so that it can be used later in the "else" case where format_spot_price_message is called
    if param1 is not None and param1.isalpha():
        currency_code = param1

    # If both parameters (price and weight) are provided, calculate the spot difference
    if param1 is not None and param2 is not None:
        # Get the conversion rate for the specified currency
        rate = 1 if currency_code == "USD" else get_exchange_rate(currency_code)
        if rate is None:
            await ctx.send(f"Error: Could not retrieve exchange rate for {currency_code}. Please try again later.")
            return
        # Convert the gold bid price to the specified currency
        gold_bid_converted = price_data['gold_bid'] * rate
        result = calculate_spot_difference(float(param1), param2, gold_bid_converted)
        await ctx.send(
            f'{TITLE_TEXT}'
            f'**{param2}oz** @ **{param1} {currency_code}** '
            f'is **{result["price_diff"]} {currency_code} {result["above_or_below"]}** the spot of {result["weighted_price"]} {currency_code} for {param2}oz\n'
            f'**{result["percent_over"]}% {result["over_or_under"]}**'
        )
    else:
        # If no parameters are provided, just send the current spot price
        await ctx.send(format_spot_price_message(price_data, currency_code))

# Run the bot with the provided Discord token
bot.run(DISCORD_TOKEN)

Hello! This is the GoldGetter bot for Discord.

The purpose of this bot is to fetch the current gold price and be a "premium calculator" for the users of the 2is1 discord server about gold and precious metals. Find me on that server as @Carmine. This bot is made just for fun and to hopefully be helpful. It runs in a lightweight docker. 

Setup requires a `.env` file with:

- `DISCORD_TOKEN`: Your bot token
- `GOLD_LOOKUP_URL`: Endpoint returning spot data (see format below)

Also ensure the Discord application has the Message Content Intent enabled.

**Usage:**

Get the spot price of gold: 
```
!gold
```
Get quick spot across available metals (gold, silver, platinum when provided by your API):
```
!spot
```
Get the spot price of fractional gold
```
!gold .5
```
Also functions as a spot calculator to check how much over/under an ask is based on the specified weight. 

```
!gold 2800 1

!gold 1400 .5
```
Any of the commands above can be converted to different currencies by adding the 3-letter currency code as the last parameter
```
!gold CAD
!gold .5 CAD
!gold 1600 .5 CAD
```

Notes
- `!spot` reports metals present in your API response. Missing fields are skipped.
- The bot uses an external FX API to convert from USD when a currency code is provided.

Enjoy

Thanks,
WrongProtocol


note: if you choose to fork this, the code is expecting the GOLD_LOOKUP_URL to return json data in the following format: 
```
{
    "goldAsk": 2621,
    "goldBid": 2617,
    "goldChange": 32.4,
    "goldChangePercent": 1.23,  
}
```

Optional fields for additional metals (shown by `!spot` if present):
```
{
    "silverAsk": 30.1,
    "silverChange": -0.2,
    "platinumAsk": 980.5,
    "platinumChange": 5.7
}
```

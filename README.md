Hello! This is the GoldGetter bot for Discord.

The purpose of this bot is to fetch the current gold price and be a "premium calculator" for the users of the 2is1 discord server about gold and precious metals. Find me on that server as @Carmine. This bot is made just for fun and to hopefully be helpful. It runs in a lightweight docker. 

there's an unpublished .env file that sets the DISCORD_TOKEN as well as the GOLD_LOOKUP_URL
so 
**you will have to fill those in with your own token / url**

**Usage:**

Get the spot price of gold: 
```
!gold
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

People keep typing !spot, but I chose not to support that because it doesn't specify which metal. This bot should be able to support other metals in the future with little legwork. 

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

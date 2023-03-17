import discord
from openexchangerates import OpenExchangeRatesClient
class Conversion:
    def __init__(self):
        self.client = OpenExchangeRatesClient('56c4524d0ab745518a4994fde36e9ee1')

    async def get_convertion_rate(self, interaction: discord.Interaction, currency_code: str, to_currency_code: str):
        await interaction.response.defer()
        latest = self.client.latest()
        currency_code = currency_code.upper()
        to_currency_code = to_currency_code.upper()
        try:
            currency = latest["rates"][currency_code]
            to_currency = latest["rates"][to_currency_code]

            conversion_Rate = (to_currency)/(currency)
            if(conversion_Rate < 0.01):
                rounded_Rate = round(conversion_Rate, 5)
            else:
                rounded_Rate = round(conversion_Rate, 2)
            await interaction.followup.send(f"1 {currency_code} ({self.get_currency_name(currency_code=currency_code)}) = {rounded_Rate} {to_currency_code} ({self.get_currency_name(currency_code=to_currency_code)})")
        except KeyError:
            await interaction.followup.send("Invalid Currency-Code!\nTo get a list of valid codes do: /currencies")

    async def get_currencies(self, interaction: discord.Interaction):
        await interaction.response.defer()
        currencies = self.client.currencies()
        codes = list(currencies.keys())
        await interaction.followup.send(f"Here is a list of valid currency-codes:\n{codes}")

    def get_currency_name(self, currency_code: str):
        currencies = self.client.currencies()

        return currencies[currency_code.upper()]
from typing import Optional

import discord
import openai
import requests
from bs4 import BeautifulSoup
from googlesearch import search


class WebsiteUtils:
    def __init__(self):
        openai.api_key = "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"        

    async def get_business_info(self, interaction: discord.Interaction, business_name: str, summarize: Optional[bool]=True, language: Optional[str]="English"):
        await interaction.response.defer()
        await interaction.followup.send("Getting business information...")
        information = self.scrape_about_us(business_name=business_name)
        if not summarize:
            if len(information) > 2000:
                await interaction.channel.send("Can't send unsummarized business information.\nSummarizing information...")
                await interaction.channel.send(self.summarize_text(text=information, language=language, business_name=business_name))
            else:
                await interaction.channel.send(information)
        else:
            await interaction.channel.send(self.summarize_text(text=information, language=language, business_name=business_name))

    def scrape_about_us(self, business_name):
        # Make a GET request to the given URL
        business_url = self.find_business_url(business_name=business_name)

        response = requests.get(business_url)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Parse the HTML content of the page
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the first link with "about" in its href
            about_link = soup.find('a', href=lambda x: 'about' in x.lower() or 'company' in x.lower() or 'ueber' in x.lower() or 'unternehmen' in x.lower())

            if about_link:
                href = about_link['href']
                if not href.startswith("http"):
                    href = business_url + href
                # If the link was found, make a GET request to its URL
                about_response = requests.get(href)
                
                # Check if the request was successful
                if about_response.status_code == 200:
                    # Parse the HTML content of the 'About Us' page
                    about_soup = BeautifulSoup(about_response.content, 'html.parser')
                    
                    # Split the about_us text into lines
                    lines = about_soup.text.splitlines()
                    lines = lines[10:]
                    # Join the lines back together, skipping any empty lines
                    filtered_lines = [line for line in lines if line.strip()]
                    about_us = '\n'.join(filtered_lines)
                    
                    return about_us
                else:
                    return 'Failed to retrieve the About Us page'
            else:
                return 'About Us link not found'
        else:
            # If the request was not successful, return an error message
            return 'Failed to retrieve the main page'

    def find_business_url(self, business_name):
        for url in search(business_name, num=1, stop=1):
            return url

    def summarize_text(self, text, language, business_name):
        # Define the model to use
        model_engine = "text-davinci-002"

        # Define the prompt for the model
        prompt = f"In {language} summarize the information about {business_name} in less than 2000 chars: " + text

        # Use the openai.Completion class to send the request
        completion = openai.Completion.create(
            engine=model_engine,
            prompt=prompt,
            max_tokens=1024,
            n=1,
            stop=None,
            temperature=0.5,
        )

        # Get the response
        summarized_text = completion.choices[0].text
        
        return summarized_text
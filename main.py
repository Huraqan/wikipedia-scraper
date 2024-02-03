################################
### venv-ws\Scripts\activate ###
### personal reminder...     ###
################################

import asyncio
import os

from time import perf_counter

from httpx import AsyncClient
from requests import Session

from src.scraper import WikipediaScraper

async def async_request(name: str, url: str, country: str, i: int):
    # Await respone
    first_paragraph = await scraper.request_wiki_page(url, country, i)
    
    # print(f"\n{name}: {first_paragraph}\n")

    return first_paragraph

async def async_loop(scraper: WikipediaScraper):
    # Create shared session for all of your requests
    async with AsyncClient() as session:
        scraper.session = session
        tasks = []

        for country, country_leaders in scraper.leaders_data.items():
            for i, leader in enumerate(country_leaders):
                tasks.append(
                    asyncio.create_task(
                        async_request(
                            leader["first_name"],
                            leader["wikipedia_url"],
                            country,
                            i,
                        )
                    )
                )

        # Now that all the tasks are registred, run them
        responses = await asyncio.gather(*tasks)

        # print(type(responses), responses)

if __name__ == "__main__":
    print(
        "\n"
        + "\n================================="
        + "\n||  POWER-DUDES Wiki-Scraper   ||"
        + "\n================================="
        + "\n"
    )
    
    picked_countries = []
    
    with Session() as session:
        scraper = WikipediaScraper(session)
        picked_countries = scraper.pick_countries()
        
        for country in picked_countries:
            scraper.get_leaders(country)
    
    scrape_t0 = perf_counter()
    asyncio.run(async_loop(scraper))
    scrape_t = perf_counter() - scrape_t0
    
    parse_t0 = perf_counter()
    scraper.parse_html()
    parse_t = perf_counter() - parse_t0
    
    print(
        f"\nTotal scraping time: {scrape_t} seconds." +
        f"\nTotal parsing time: {parse_t} seconds.\n"
    )
    
    scraper.to_json_file("output_json.json")
    scraper.to_csv_file("output_csv.csv")
    scraper.to_all_text_file("all_text.txt")
    
    print(f"\n\nALL DONE! Successfully scraped scoundrels from: {picked_countries}\n\n")
    
    input("Press ENTER to quit: ")
    # os.system('pause')

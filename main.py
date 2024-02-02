################################
### venv-ws\Scripts\activate ###
### personal reminder...     ###
################################

from requests import Session

from src.scraper import WikipediaScraper


def pick_countries(scraper) -> list:
    countries = scraper.get_countries()
    
    while True:
        answer = input(
            f"\nPick one or more countries from {countries}"
            + " separated by a comma or pick 'all': "
        )
        
        if answer == "all":
            return countries
        
        answer_list = answer.replace(" ", "").lower().split(",")
        answer_list = [answer for answer in answer_list if answer in countries]
        
        if len(answer_list) > 0:
            return answer_list
        else:
            print("\nWrong input. Two letters per country, separated by a comma.\n")


if __name__ == "__main__":
    print(
        "\n" +
        "\n=================================" +
        "\n||  POWER-DUDES Wiki-Scraper   ||" +
        "\n=================================" +
        "\n"
    )
    with Session() as session:
        scraper = WikipediaScraper(session)
        
        for country in pick_countries(scraper):
            scraper.get_leaders(country)
        
        for (country, country_leaders) in scraper.leaders_data.items():
            print("\n    country:", country)
            
            for i, leader in enumerate(country_leaders):
                first_paragraph = scraper.get_first_paragraph(leader["wikipedia_url"], country, i)
                
                print(f"\n{leader["first_name"]}: {first_paragraph}\n")
    
    scraper.to_json_file("output_json.json")
    scraper.to_csv_file("output_csv.csv")

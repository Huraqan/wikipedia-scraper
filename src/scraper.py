# import csv
import json
from re import compile

from pandas import DataFrame
from bs4 import BeautifulSoup
from requests import Session

# my_dict.pop("key", None)
# del my_dict["key"]

class WikipediaScraper:
    """
    WikipediaScraper class for scraping the first paragraph of country leaders biographies.
    Will use an API to request a list of countries and their leaders and use that to locate
    their wikipedia page.
    """

    def __init__(self, session: Session):
        self.session: Session = session
        self.leaders_data: dict = {}
        ## API
        self.base_url: str = "https://country-leaders.onrender.com"
        self.countries_endpoint: str = "/countries"
        self.leaders_endpoint: str = "/leaders"
        self.cookies_endpoint: str = "/cookie"
        self.check_endpoint: str = "/check"
        self.cookie: object = self.request_cookie()
        ## REGEX
        self.compiled_brackets = compile(r"\[[^\]]*\]")
        self.compiled_parentheses = compile(r"(\(/[^\)]+\)|\( ?\))")
        self.compiled_commas = compile(r" ?,( *,)*")
        self.compiled_spaces = compile(r"  +")
        self.compiled_par_comma = compile(r"\(, ?")

    def try_except_decorator(function):
        def decorated(*args, **kwargs):
            while True:
                try:
                    return function(*args, **kwargs)
                except:
                    if input("\nCONNECTION ERROR! Try again? 'n' to quit : ") == "n":
                        exit()

        return decorated

    @try_except_decorator
    def make_simple_request(self, url: str):
        return self.session.get(url)

    @try_except_decorator
    def make_api_request(self, endpoint="", cookies=None, params={}):
        return self.session.get(
            self.base_url + endpoint, cookies=cookies, params=params
        )
    
    def refresh_cookie(self) -> object:
        """Checks the API cookie status, returning the existing or new cookie object."""
        print("\nChecking if cookie is still valid...")

        check_request = self.make_api_request(self.check_endpoint, self.cookie)

        match check_request.status_code:
            case 200:
                print(f"\nStatus: {check_request.status_code} Cookie still fresh. Using cookie.")
                return self.cookie
            case 422:
                print(f"\nStatus: {check_request.status_code} Cookie stale! Refreshing cookie...")
            case 403:
                print(f"\nStatus: {check_request.status_code} FORBIDDEN")

        return self.request_cookie()

    def request_cookie(self) -> object:
        """Requests the API cookie and returns the new cookie object."""
        while True:
            print("\nRequesting a new cookie...")

            cookie_request = self.make_api_request(self.cookies_endpoint)

            self.cookie = cookie_request.cookies

            match cookie_request.status_code:
                case 200:
                    print("Cookie request status: OK")
                    return self.cookie
                case 400:
                    print("Cookie request status: BAD REQUEST")
                case 403:
                    print("Cookie request status: FORBIDDEN")
                case 404:
                    print("Cookie request status: PAGE NOT FOUND")

            answer = input("\nFailed to get a cookie, try again? 'n' to quit: ")
            if answer == "n":
                exit()

    def get_countries(self) -> list:
        """Retrieves a list of supported countries from the API."""
        countries_request = self.make_api_request(self.countries_endpoint, self.cookie)
        return countries_request.json()

    def get_leaders(self, country: str) -> None:
        """Retrieves and populate leaders_data with the leaders of a specific country."""
        print(f"\nRequesting leaders from {country.upper()}...")

        leaders_request = self.make_api_request(
            endpoint=self.leaders_endpoint,
            cookies=self.refresh_cookie(),
            params={"country": country},
        )

        country_leaders = leaders_request.json()
        self.leaders_data[country] = country_leaders
    
    async def request_wiki_page(self, wikipedia_url: str, country: str, i: int) -> str:
        """Request and store html content of leader wikipedia page using AsyncClient"""
        print(f"\n    STARTING SCRAPING OF {wikipedia_url[:40]}...")
        
        wikipedia_request = await self.make_simple_request(wikipedia_url)
        self.leaders_data[country][i]["wikipedia_html"] = wikipedia_request.text
        self.leaders_data[country][i]["paragraph"] = "Text not parsed yet..."
        return "Text not parsed yet..."

    def parse_html(self):
        for country, country_leaders in self.leaders_data.items():
            for i, leader in enumerate(country_leaders):
                paragraph = self.parse_first_paragraph(leader["wikipedia_url"], country, i)
                
                print(f"\n{leader["first_name"]}: {paragraph}\n")

    def parse_first_paragraph(self, wikipedia_url: str, country: str, i: int) -> str:
        """Parses the html content and both stores and returns first paragraph."""
        print(f"\nPARSING:  {wikipedia_url}\n")
    
        soup = BeautifulSoup(self.leaders_data[country][i]["wikipedia_html"], "html.parser")

        ## Narrowing it down to the content div
        content_div = soup.find(
            name="div", attrs={"class": "mw-content-ltr mw-parser-output"}
        )
        if content_div is None:
            print("Can't find ltr content div, searching for rtl content...\n")
            content_div = soup.find(
                name="div", attrs={"class": "mw-content-rtl mw-parser-output"}
            )
        if content_div is None:
            print("Can't find rtl content, continuing with full page...\n")
            content_div = soup

        ## Cleaning of all intrusive and unnecessary divs
        for tag in content_div.find_all(name="div"):
            tag.decompose()

        ## Finding the first paragraph
        for paragraph in content_div.find_all(name="p"):
            if not paragraph.find(name="b"):
                continue

            ## Deleting sup tags
            for sup_tag in paragraph.find_all(name="sup"):
                print("- Decomposing <sup> tag:", sup_tag.text)
                sup_tag.decompose()
            
            for span_tag in paragraph.find_all(name="span"):
                print("- Decomposing <span> tag:", span_tag.text)
                span_tag.decompose()
            
            # print(f"\nFINAL SOUP: {paragraph}\n")

            ## Regex cleanup
            paragraph_text = self.clean_text(paragraph.text)

            ## Store in dict
            self.leaders_data[country][i]["paragraph"] = paragraph_text
            
            del self.leaders_data[country][i]["wikipedia_html"]
            
            return paragraph_text#[:70] + "..."

        return "\n\n    !!! NOTING FOUND !!!\n\n"

    # @staticmethod
    def clean_text(self, text: str) -> str:
        """
        Returns the passed string cleaned of (most) undesired parts.
        Removes brackets and spacial parentheses cases, and their content.
        Removes extra successive commas, and all extra spaces.
        """
        text_length = len(text)

        text = self.compiled_brackets.sub("", text)
        text = self.compiled_parentheses.sub("", text)
        text = self.compiled_spaces.sub(" ", text)
        text = self.compiled_commas.sub(",", text)
        text = self.compiled_par_comma.sub("(", text)

        if text_length > len(text):
            print(f"- Regex shortened text by: {text_length - len(text)} characters.")
        else:
            print("- Regex had nothing to clean up...")

        return text
    
    def to_all_text_file(self, filename: str):
        with open(filename, "w+") as file:
            for leaders in self.leaders_data.values():
                for leader in leaders:
                    try:
                        file.write(f"{leader['first_name']} {leader['last_name']} : {leader['paragraph']}\n")
                    except:
                        file.write(f"{leader['first_name']} {leader['last_name']} : COULD NOT WRITE DATA\n")
            print(f"Saved TXT file as: {filename}")
    
    def to_json_file(self, filename: str):
        """
        Stores the data structure into a JSON file with the specified name.
        """
        with open(filename, "w") as file:
            json.dump(self.leaders_data, file)
            print(f"Saved JSON file as: {filename}")
        
    
    def to_csv_file(self, filename: str):
        """
        Stores the data structure into a CSV file with the specified name.
        """
        leaders_summary: list = []

        for country, leaders in self.leaders_data.items():
            for leader in leaders:
                leaders_summary.append(
                    {
                        "Country": country,
                        "Leader": f"{leader["first_name"]} {leader["last_name"]}",
                        "First Paragraph": leader["paragraph"],
                    }
                )

        df = DataFrame.from_dict(leaders_summary)
        df.to_csv(filename, index=False, header=True)
        print(f"Saved CSV file as: {filename}")
    
    def pick_countries(self) -> list:
        countries = self.get_countries()

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

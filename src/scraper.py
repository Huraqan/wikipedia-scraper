# import csv
import json
from re import compile

from pandas import DataFrame
from bs4 import BeautifulSoup
from requests import Session


class WikipediaScraper:
    """
    WikipediaScraper class for scraping the first paragraph of country leaders biographies.
    Will use an API to request a list of countries and their leaders and use that to locate
    their wikipedia page.
    """

    def __init__(self, session: Session):
        self.base_url: str = "https://country-leaders.onrender.com"
        self.country_endpoint: str = "/countries"
        self.leaders_endpoint: str = "/leaders"
        self.cookies_endpoint: str = "/cookie"
        self.check_endpoint: str = "/check"
        self.leaders_data: dict = {}
        self.session: Session = session
        self.cookie: object = self.request_cookie()

    def refresh_cookie(self) -> object:
        """Checks the API cookie status, returning the existing or new cookie object."""

        print("\nChecking if cookie is still valid...")

        check_request = self.session.get(
            self.base_url + self.check_endpoint, cookies=self.cookie
        )

        match check_request.status_code:
            case 200:
                print("\nCookie still valid.")
                return self.cookie
            case 422:
                print("\nCookie stale! Refreshing cookie...")
            case _:
                print(f"\nStatus: {check_request.status_code}")

        return self.request_cookie()

    def request_cookie(self) -> object:
        """Requests the API cookie and returns the new cookie object."""
        print("\nRequesting a new cookie...")

        cookie_request = self.session.get(self.base_url + self.cookies_endpoint)

        match cookie_request.status_code:
            case 200:
                print("Cookie request status: OK")
            case 400:
                print("Cookie request status: BAD REQUEST")
            case 403:
                print("Cookie request status: FORBIDDEN")
            case 404:
                print("Cookie request status: PAGE NOT FOUND")

        if not cookie_request.status_code == 200:
            return None

        self.cookie = cookie_request.cookies

        return self.cookie

    def get_countries(self) -> list:
        """Retrieve a list of supported countries from the API."""
        countries_request = self.session.get(
            self.base_url + self.country_endpoint, cookies=self.cookie
        )
        return countries_request.json()

    def get_leaders(self, country: str) -> None:
        """
        Retrieve and populate leaders_data with the leaders of a specific country.

        - country (str): The name of the country for which leaders are retrieved.
        """
        print(f"\nRequesting leaders from {country.upper()}...")

        req_leaders = self.session.get(
            self.base_url + self.leaders_endpoint,
            params={"country": country},
            cookies=self.refresh_cookie(),
        )

        country_leaders = req_leaders.json()
        self.leaders_data[country] = country_leaders

    def get_first_paragraph(self, wikipedia_url: str, country: str, i: int) -> str:
        """
        Retrieve and return the first paragraph from a Wikipedia URL.

        - wikipedia_url (str): The URL of the Wikipedia page.
        """
        print(f"\n{wikipedia_url}\n")

        soup = BeautifulSoup(self.session.get(wikipedia_url).text, "html.parser")

        content_div = soup.find(
            name="div", attrs={"class": "mw-content-ltr mw-parser-output"}
        )

        if content_div is None:
            print("\nCan't find ltr content div, searching for rtl content...")
            content_div = soup.find(
                name="div", attrs={"class": "mw-content-rtl mw-parser-output"}
            )
        if content_div is None:
            print("\nCan't find rtl content, continuing with full page...")
            content_div = soup

        for tag in content_div.find_all(name="div"):
            tag.decompose()

        for tag in content_div.find_all(name="p"):
            if not tag.find(name="b"):
                continue

            for sup_tag in tag.find_all(name="sup"):
                print("- Decomposing <sup> tag:", sup_tag.text)
                sup_tag.decompose()

            self.leaders_data[country][i]["paragraph"] = tag.text

            return tag.text

        return "\n\n    !!! NOTING FOUND !!!\n\n"

    @staticmethod
    def clean_text(text: str) -> str:
        """
        Returns the passed string cleaned of (most) undesired parts.
        Removes brackets and spacial parentheses cases, and their content.
        Removes extra successive commas, and all extra spaces.
        """
        compiled_brackets = compile(r"\[[^\]]*\]")
        compiled_parentheses = compile(r"\(/[^\)]+\)")
        compiled_commas = compile(r" ?,( *,)*")
        compiled_spaces = compile(r"  +")

        text_length = len(text)

        text = compiled_brackets.sub("", text)
        text = compiled_parentheses.sub("", text)
        text = compiled_spaces.sub(" ", text)
        text = compiled_commas.sub(",", text)

        if text_length > len(text):
            print(f"- Regex shortened text by: {text_length - len(text)} characters.")
        else:
            print("- Regex had nothing to clean up...")

        return text

    def to_json_file(self, filename: str):
        """
        Store the data structure into a JSON file with the specified name.
        """
        with open(filename, "w") as file:
            json.dump(self.leaders_data, file)

    def to_csv_file(self, filename: str):
        """
        Store the data structure into a CSV file with the specified name.
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

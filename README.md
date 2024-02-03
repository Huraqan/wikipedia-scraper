# POWER-DUDES Wiki-Scraper
![python version](https://img.shields.io/badge/python-v3.12.1-green?logo=python) ![build version](https://img.shields.io/badge/build-v0.07-blue)

## Description
This script will query an API for a list of high ranking scumbags from vairous countries.
First paragraphs of biographies will subsequently be scraped from wikipedia for each and every scumbag.

Data will be stored as a `JSON` file, and a smaller amount of data will be stored as a `CSV` file.
A compilation of all paragraphs will also be saved to a `TXT` file.
Some paragraphs might not be stored succesfully in the txt file due to current limitations that are being worked on. 

**NOW USING ASYNCIO FOR MUCH FASTER REQUESTS**

## Version history
**---- v 0.07:**
- Multiprocessing: Implemented faster requests with AsyncClient
- Text cleanup: Improved BS4 tag filtering
- Text cleanup: Improved REGEX filtering

## Setup
- Python interpreter is needed: install python from https://www.python.org/downloads/
- Make sure to install the required packages by executing the following command: `pip install -r requirements.txt`

## Usage
Double click the `main.py` file to launch the script.
Alternatively you an execute from an open terminal, from the project directory: `python main.py`

You can pick a country from a list provided by the api.

Data is stored as `output_json.json`, `output_csv.scv` and `all_text.txt`.

Note that the `JSON` file will contain all data including details on each leader.

Data in the `CSV` file will be limited to the following fields: `Country`, `Leader` and `Paragraph`.

For the `TXT` file, data will only consist of a compilation of a leader name and its associated paragraph. All text might not always be successfully written to the `TXT` file due to special character encodings.

## Enjoy scraping scoundrels!
![alt text](image.png)
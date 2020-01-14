#!/usr/bin/env python3
import argparse
import requests
from sys import exit
from time import sleep
from random import choice
from threading import Thread
from bs4 import BeautifulSoup
from progressbar import ProgressBar
import xlwt
requests.packages.urllib3.disable_warnings()
USER_AGENTS = [line.strip() for line in open('user_agents.txt')]
class ScrapeEngine():
    URL = {'google': 'https://www.google.com/search?q=site:linkedin.com/in+"{}"&num=100&start={}',
           'bing': 'https://www.bing.com/search?q=site:linkedin.com/in+"{}"&first={}'}
    def __init__(self):
        self.linkedin = {}
        self.running = True
    def timer(self, time):
        sleep(time)
        self.running = False
    def search(self, search_engine, company_name, timeout, jitter):
        self.running = True  # Define search as "running" after init(), not used in DNS_Enum
        Thread(target=self.timer, args=(timeout,), daemon=True).start()  # Start timeout thread
        self.search_links = 0  # Total Links found by search engine
        self.name_count = 0  # Total names found from linkedin
        found_names = 0  # Local count to detect when no new names are found
        while self.running:
            if self.search_links > 0 and found_names == self.name_count:
                return self.linkedin
            found_names = self.name_count
            self.name_search(search_engine, self.search_links, company_name, jitter)
        return self.linkedin
    def name_search(self, search_engine, count, company_name, jitter):
        url = self.URL[search_engine].format(company_name, count)
        for link in get_links(get_request(url, 3)):
            url = str(link.get('href')).lower()
            if (search_engine+".com") not in url and not url.startswith("/"):
                self.search_links += 1
                if "linkedin.com/in" in url and self.extract_linkedin(link, company_name) :
                    self.name_count += 1
        sleep(jitter)
    def extract_linkedin(self, link, company_name):
        if debug:
            print("[*] Parsing Linkedin User: {}".format(link.text))
        if safe and company_name.lower() not in link.text.lower():
            return False
        try:
            x = link.text.split("|")[0]
            x = x.split("...")[0]
            # Extract Name (if title provided)
            if "–" in x:
                name = link.text.split("–")[0].rstrip().lstrip()
            elif "-" in x:
                name = link.text.split("-")[0].rstrip().lstrip()
            elif "|" in x:
                name = link.text.split("|")[0].rstrip().lstrip()
            else:
                name = x
            try:
                # Quick split to extract title, but focus on name
                title = link.text.split("-")[1].rstrip().lstrip()
                if "..." in title:
                    title = title.split("...")[0].rstrip().lstrip()
                if "|" in title:
                    title = title.split("|")[0].rstrip().lstrip()
            except:
                title = "N/A"
            tmp = name.split(' ')
            name = ''.join(e for e in tmp[0] if e.isalnum()) + " " + ''.join(e for e in tmp[1] if e.isalnum())
            # Catch 1st letter last name: Fname L.
            tmp = name.split(' ')
            if len(tmp[0]) <= 1 or len(tmp[-1]) <=1:
                raise Exception("\'{}\' Failed name parsing".format(link.text))
            elif tmp[0].endswith((".","|")) or tmp[-1].endswith((".","|")):
                raise Exception("\'{}\' Failed name parsing".format(link.text))
            if name not in self.linkedin:
                self.linkedin[name] = {}
                self.linkedin[name]['last'] = name.split(' ')[1].lower().rstrip().lstrip()
                self.linkedin[name]['first'] = name.split(' ')[0].lower().rstrip().lstrip()
                self.linkedin[name]['title'] = title.strip().lower().rstrip().lstrip()
                return True
        except Exception as e:
            if debug:
                print("[!] Debug: {}".format(str(e)))
        return False
def get_links(raw_response):
    # Returns a list of links from raw requests input
    links = []
    soup = BeautifulSoup(raw_response.content, 'html.parser')
    for link in soup.findAll('a'):
        try:
            links.append(link)
        except:
            pass
    return links
def get_request(link, timeout):
    # HTTP(S) GET request w/ user defined timeout
    head = {
        'User-Agent': '{}'.format(choice(USER_AGENTS)),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'}
    return requests.get(link, headers=head, verify=False, timeout=timeout)
def main(args):
    found_names = {}
    search = ['google', 'bing']
    banner()
    q = 1
    w = 2 # NOTE: Variable W is for when working within spreadsheet. Python starts at 0 and counts upwards from there. Excel starts at 1, causing there to be a downwards shift in cells within formulas.
    wb = xlwt.Workbook()
    ws = wb.add_sheet('Scraped LinkedIn Employees', cell_overwrite_ok=True)
    compname = args.company_name
    compname = compname[:-4] + "Scraped.xls"
    ws.write(0,0,"First Name:")
    ws.write(0,1, "Last Name:")
    ws.write(0,2, "Job Title:")
    ws.write(0,3, "Email:")
    
    for site in search:
        lkin = ScrapeEngine().search(site, args.company_name, args.timeout, args.jitter)
        if lkin:
            for name, data in lkin.items():
                ws.write(q,0,data['first'])
                ws.write(q,1,data['last'])
                ws.write(q,2,data['title'])
                ws.write(q,3,xlwt.Formula('CONCATENATE(LEFT(A%s,1),B%s,"@%s")' % (w, w, args.company_name)))
                w = w + 1
                q = q + 1
                id = data['first'] + ":" + data['last']
                if name and id not in found_names:
                    found_names[id] = data
        wb.save(compname)
def banner():
    print("""

 /$$                             /$$     /$$       /$$           /$$                       /$$
| $$                            | $$    | $$      |__/          | $$                      | $$
| $$        /$$$$$$   /$$$$$$  /$$$$$$  | $$       /$$ /$$$$$$$ | $$   /$$  /$$$$$$   /$$$$$$$
| $$       /$$__  $$ /$$__  $$|_  $$_/  | $$      | $$| $$__  $$| $$  /$$/ /$$__  $$ /$$__  $$
| $$      | $$$$$$$$| $$$$$$$$  | $$    | $$      | $$| $$  \ $$| $$$$$$/ | $$$$$$$$| $$  | $$
| $$      | $$_____/| $$_____/  | $$ /$$| $$      | $$| $$  | $$| $$_  $$ | $$_____/| $$  | $$
| $$$$$$$$|  $$$$$$$|  $$$$$$$  |  $$$$/| $$$$$$$$| $$| $$  | $$| $$ \  $$|  $$$$$$$|  $$$$$$$
|________/ \_______/ \_______/   \___/  |________/|__/|__/  |__/|__/  \__/ \_______/ \_______/
                                                                                              
Based off of https://github.com/m8r0wn/CrossLinked
Modified by Ronnie Bartwitz
""")
if __name__ == '__main__':
    VERSION = "0.1.0"
    args = argparse.ArgumentParser(description="", formatter_class=argparse.RawTextHelpFormatter, usage=argparse.SUPPRESS)
    args.add_argument('-t', dest='timeout', type=int, default=25,help='Timeout [seconds] for search threads (Default: 25)')
    args.add_argument('-j', dest='jitter', type=float, default=0,help='Jitter for scraping evasion (Default: 0)')
    args.add_argument('-f', dest='nformat', type=str, required=True, help='Format names, ex: \'domain\{f}{last}\', \'{first}.{last}@domain.com\'')
    args.add_argument('-s', "--safe", dest="safe", action='store_true',help="Only parse names with company in title (Reduces false positives)")
    args.add_argument(dest='company_name', nargs='+', help='Target company name')
    args = args.parse_args()
    safe = args.safe
    debug = False
    args.company_name = args.company_name[0]
    try:
        main(args)
    except KeyboardInterrupt:
        print("[!] Key event detected, closing...")
        exit(0)
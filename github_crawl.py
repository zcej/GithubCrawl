import json
from urllib import parse

import requests
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings()

USERNAME = ""
PASSWD = ""
START_PAGE = 1
END_PAGE = 2
KEYWORD = ""
PROXY = {"http": "112.6.117.135:8085"}  # https://free.kuaidaili.com/free/inha/


class GithubCrawl:
    def __init__(self, username, passwd, start_page, end_page, keyword):
        self.username = username
        self.passwd = passwd
        self.start_page = start_page
        self.end_page = end_page

        self.session = requests.Session()
        self.result = []
        self.output_file = "./temp.txt"

        self.login_url = "https://github.com/login"
        self.post_url = "https://github.com/session"
        self.search_url = f"https://github.com/search?q={keyword}&type=code"
        self.headers = {
            "Referer": "https://github.com/",
            "Host": "github.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36",
        }
        self.proxy = {
            "http": "112.6.117.135:8085"
        }

    @staticmethod
    def _parse_content(tags):
        content = ""
        for tag in tags:
            content += tag.text
        return content

    def _get_token(self):
        resp = self.session.get(self.login_url, headers=self.headers, verify=False, proxies=self.proxy)
        soup = BeautifulSoup(resp.text, "lxml")
        token = soup.find("input", attrs={"name": "authenticity_token"}).get("value")
        print(f"token is: {token}")
        return token

    def login(self, token):
        post_data = {
            'commit': 'Sign in',
            'utf8': '✓',
            'login': self.username,
            'password': self.passwd,
            'authenticity_token': token
        }
        resp = self.session.post(self.post_url, data=post_data, headers=self.headers, verify=False)
        if resp.status_code == 200:
            print("successful login to github...")
            self.parse_search_page()

    def parse_search_page(self):
        for i in range(self.start_page - 1, self.end_page):
            url = self.search_url + f"&p={i + 1}"
            print(f"url is: {url}")
            resp = self.session.get(url, headers=self.headers, verify=False, proxies=self.proxy)
            soup = BeautifulSoup(resp.text, "lxml")
            items = soup.find_all(class_="code-list-item")
            if not items:
                print(f"not found data in the page {i}...")
                break
            for item in items:
                text_small = item.find(class_="text-small").text.strip().split("/")
                lang = item.find(attrs={"itemprop": "programmingLanguage"})
                data = {
                    "author_favicon": item.find("img").attrs["src"],
                    "author": text_small[0].strip(),
                    "repository": text_small[1].strip(),
                    "filename": item.find(class_="text-normal").text.strip(),
                    "filepath": parse.urljoin("https://github.com", item.find(class_="text-normal").a.attrs["href"]),
                    "content": self._parse_content(item.find_all(class_="blob-code")),
                    "language": lang.text if lang else lang,
                    "updated_at": item.find(class_="updated-at").find(class_="no-wrap").attrs["datetime"]
                }
                print(data)
                self.result.append(json.dumps(data))

    def write_to_file(self):
        try:
            with open(self.output_file, "w", encoding="utf-8") as f:
                f.writelines([line + "\n" for line in self.result])
            print("finished...")
        except Exception as e:
            print("write result to file failed...")
            raise e

    def start(self):
        token = self._get_token()
        self.login(token)
        self.write_to_file()


def main():
    crawler = GithubCrawl(USERNAME, PASSWD, START_PAGE, END_PAGE, KEYWORD)
    crawler.start()


if __name__ == '__main__':
    main()

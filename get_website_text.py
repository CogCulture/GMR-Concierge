"""Copies the text of the pages listed in pages.txt into website_info.txt."""
import os
from datetime import date
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

FOLDER = os.path.dirname(os.path.abspath(__file__))


def path(name: str) -> str:
    return os.path.join(FOLDER, name)


def page_text(url: str) -> str:
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")
    # Remove code, menus and footers, which are not page information
    for tag in soup(["script", "style", "noscript", "nav", "header", "footer"]):
        tag.decompose()
    # Keep each link next to its text, so the chatbot can share it
    for a in soup.find_all("a", href=True):
        target = urljoin(url, a["href"])
        if target.startswith(("http", "tel:", "mailto:")) and not a["href"].startswith("#"):
            a.append(f" [link: {target}]")
    return soup.get_text("\n", strip=True)


def main():
    with open(path("pages.txt"), encoding="utf-8") as f:
        links = [line.strip() for line in f if line.strip().startswith("http")]

    blocks, failed = [], []
    for link in links:
        try:
            text = page_text(link)
            if len(text) < 200:
                raise ValueError("very little text found")
            blocks.append(f"LINK: {link}\nCOPIED ON: {date.today():%d %B %Y}\n{text}")
            print(f"OK      {len(text.split()):>6} words  {link}")
        except Exception as e:
            failed.append(link)
            print(f"FAILED  {link}  ({e})")

    if not blocks:
        print("Nothing was copied, so website_info.txt was left unchanged.")
        return

    # Facts you type yourself go in extra_info.txt, so a new run never erases them
    if os.path.exists(path("extra_info.txt")):
        with open(path("extra_info.txt"), encoding="utf-8") as f:
            blocks.append("EXTRA INFORMATION:\n" + f.read())

    result = "\n\n==========\n\n".join(blocks)
    with open(path("website_info.txt"), "w", encoding="utf-8") as f:
        f.write(result)
    print(f"\nSaved {len(links) - len(failed)} of {len(links)} pages, {len(result.split())} words in total.")


if __name__ == "__main__":
    main()

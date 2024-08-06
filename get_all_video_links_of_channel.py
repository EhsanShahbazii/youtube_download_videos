from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import time
import asyncio

url = str(input('send piped channel url: '))

async def scroll_page_to_bottom(page):
    last_height = await page.evaluate("document.body.scrollHeight")

    while True:
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = await page.evaluate("document.body.scrollHeight")
        print('scrolling the page ...')

        if new_height == last_height:
            break
        last_height = new_height


async def main(url):
    async with async_playwright() as p:
        print('launching the browser ...')
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto(url)

        await scroll_page_to_bottom(page)

        print('getting the html file ...')
        html = await page.inner_html(".video-grid")
        soup = BeautifulSoup(html, 'html.parser')

        await browser.close()

        video_links = []
        for video in soup.select('a.inline-block'):
            video_links.append(f"https://youtube.com{video['href']}")

        with open("video_links.txt", 'w') as file2write:
            for line in video_links:
                file2write.write(line + '\n')

        print('video links saved!')


asyncio.run(main(url))

import time
import os
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from telegram import Bot

# Configuration
TELEGRAM_TOKEN = "8150136049:AAH1nLTe3rn80g9ONUbogVD4cUApZenSleY"
CHANNEL_ID = "@animeencodetest"  # Your Telegram channel ID
TWITTER_USERNAME = "AniNewsAndFacts"  # Twitter username to scrape

def init_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_service = ChromeService(executable_path='path/to/chromedriver')  # Update the path to your ChromeDriver
    driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
    return driver

def download_media(url):
    response = requests.get(url)
    filename = url.split("/")[-1]  # Extract the filename from the URL
    with open(filename, 'wb') as file:
        file.write(response.content)
    return filename

def fetch_latest_posts():
    driver = init_driver()
    driver.get(f'https://twitter.com/{TWITTER_USERNAME}')
    time.sleep(5)  # Wait for the page to load

    try:
        tweets = driver.find_elements(By.XPATH, '//article[@data-testid="tweet"]')
        posts = []

        for tweet in tweets[:5]:  # Get the latest 5 tweets
            tweet_id = tweet.get_attribute('data-tweet-id')
            tweet_text = tweet.find_element(By.XPATH, './/div[@lang]').text
            
            # Check for media (images/videos)
            media = tweet.find_elements(By.XPATH, './/div[contains(@data-testid, "media")]')
            media_urls = []
            for item in media:
                video = item.find_elements(By.TAG_NAME, 'video')
                if video:
                    media_urls.append(video[0].get_attribute('src'))  # Get video URL
                else:
                    images = item.find_elements(By.TAG_NAME, 'img')
                    if images:
                        media_urls.append(images[0].get_attribute('src'))  # Get image URL

            posts.append({
                'id': tweet_id,
                'text': tweet_text,
                'media': media_urls
            })

        return posts
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        driver.quit()
    
    return []

def send_to_telegram(posts):
    bot = Bot(token=TELEGRAM_TOKEN)

    for post in posts:
        caption = post['text']
        media_urls = post['media']
        
        for media_url in media_urls:
            local_filename = download_media(media_url)
            if media_url.endswith('.mp4'):
                bot.send_video(chat_id=CHANNEL_ID, video=open(local_filename, 'rb'), caption=caption)
            else:
                bot.send_photo(chat_id=CHANNEL_ID, photo=open(local_filename, 'rb'), caption=caption)

            os.remove(local_filename)  # Remove the file after sending

def main():
    while True:
        latest_posts = fetch_latest_posts()
        if latest_posts:
            send_to_telegram(latest_posts)
        time.sleep(60)  # Check every minute

if __name__ == '__main__':
    main()

import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Setup Chrome
options = webdriver.ChromeOptions()
options.add_experimental_option("detach", True)  # keep browser open
options.add_argument("start-maximized")
browser = webdriver.Chrome(options=options)
wait = WebDriverWait(browser, 20)  # longer wait

# Keyword and page
keyword = "price"
page_num = 1

# Storage
posts = {"writer": [], "date": [], "location": [], "text": []}
collected = 0
target = 1000

while collected < target:
    print(f"Working on page {page_num}...")

    # Build search URL
    url = f"https://community.withairbnb.com/t5/forums/searchpage/tab/message?filter=location&q={keyword}&location=category:community-center&page={page_num}&collapse_discussion=true"
    browser.get(url)
    time.sleep(3)

    # Find all post links on current page
    try:
        titles = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.MessageSubject a[class*="page-link"]'))
        )
    except:
        print("⚠️ No posts found on this page.")
        break

    for title in titles:
        if collected >= target:
            break

        link = title.get_attribute("href")
        if not link:
            continue

        # Open post in new tab
        try:
            browser.execute_script("window.open(arguments[0]);", link)
            browser.switch_to.window(browser.window_handles[-1])
        except Exception as e:
            print(f"⚠️ Could not open link: {e}")
            continue

        try:
            # Retry logic for writer
            writer = "N/A"
            for attempt in range(2):
                try:
                    writer = wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'div#messageView2_1 div.user-rank a[target="_self"]'))
                    ).text
                    break
                except:
                    if attempt == 0:
                        print("Retrying writer...")
                        time.sleep(3)

            # Date
            try:
                date = browser.find_element(By.CSS_SELECTOR, 'div#messageView2_1 div[class*=header-full] span.DateTime').text
            except:
                date = "N/A"

            # Location (optional)
            try:
                location = browser.find_element(By.CSS_SELECTOR, 'div#messageView2_1 div[class*=header-full] span[class*="location"]').text
            except:
                location = "N/A"

            # Full text (all paragraphs combined)
            try:
                paragraphs = browser.find_elements(By.CSS_SELECTOR, 'div#messageView2_1 div.lia-message-body-content > p')
                full_text = " ".join([p.text for p in paragraphs])
            except:
                full_text = ""

            # Store
            posts["writer"].append(writer)
            posts["date"].append(date)
            posts["location"].append(location)
            posts["text"].append(full_text)

            collected += 1
            print(f"✅ Collected {collected}")

            # Save backup every 50 posts
            if collected % 50 == 0:
                pd.DataFrame(posts).to_csv("airbnb_posts_backup.csv", index=False, encoding="utf-8-sig")
                print("💾 Backup saved")

            # Refresh browser every 100 posts
            if collected % 100 == 0:
                browser.refresh()
                time.sleep(2)

        except Exception as e:
            print(f"⚠️ Error scraping post: {e}")

        finally:
            # Always close tab and go back
            if len(browser.window_handles) > 1:
                browser.close()
                browser.switch_to.window(browser.window_handles[0])
            time.sleep(1)

    # Next page
    page_num += 1

# Final save
df = pd.DataFrame(posts)
df.to_csv(f"airbnb_community_{keyword}.csv", index=False, encoding="utf-8-sig")
print(f"🎉 Done! Saved {collected} posts to airbnb_community_posts.csv")

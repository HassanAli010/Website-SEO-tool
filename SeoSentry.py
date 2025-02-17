import requests
from bs4 import BeautifulSoup
import streamlit as st
from urllib.parse import urljoin, urlparse
from sklearn.feature_extraction.text import TfidfVectorizer
import ssl
import re
import matplotlib.pyplot as plt
import time
import smtplib
from email.mime.text import MIMEText

st.title('Website Monitoring & SEO Performance Tool')

url = st.text_input('Enter Website URL (e.g., https://growthaccess.ae/)')

# Uptime Monitoring
st.sidebar.header('Uptime Monitoring')
uptime_check = st.sidebar.checkbox('Enable Uptime Monitoring')

# Email Alerts
st.sidebar.header('Email Alerts')
email_alerts = st.sidebar.checkbox('Enable Email Alerts')
recipient_email = st.sidebar.text_input('Recipient Email')

if url:
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # 1. Website Speed (Basic Load Time Check)
        load_time = response.elapsed.total_seconds()
        st.write(f"**Website Load Time:** {load_time:.2f} seconds")

        # 2. Meta Tag Analysis
        title_tag = soup.title.text if soup.title else 'N/A'
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        meta_desc = meta_desc['content'] if meta_desc else 'N/A'
        h1_tag = soup.find('h1').text.strip() if soup.find('h1') else 'N/A'

        st.write(f"**Title:** {title_tag}")
        st.write(f"**Meta Description:** {meta_desc}")
        st.write(f"**H1 Tag:** {h1_tag}")
        

        # 3. Broken Links Checker
        broken_links = []
        all_links = [urljoin(url, a['href']) for a in soup.find_all('a', href=True)]
        valid_links = set([link for link in all_links if urlparse(link).netloc])
        
        for link in valid_links:
            try:
                link_response = requests.head(link, timeout=5)
                if link_response.status_code >= 400:
                    broken_links.append(link)
            except:
                broken_links.append(link)
        
        st.write(f"**Broken Links Found:** {len(broken_links)}")
        for link in broken_links:
            st.write(link)

        # 4. SSL Certificate Validation
        try:
            ssl_response = requests.get(url, timeout=5, verify=True)
            st.write("**SSL Certificate Status:** Valid")
        except requests.exceptions.SSLError:
            st.write("**SSL Certificate Status:** Invalid")

        # 5. Mobile Responsiveness (Viewport Check)
        viewport_meta = soup.find('meta', attrs={'name': 'viewport'})
        if viewport_meta:
            st.write("**Mobile Friendly:** Viewport meta tag detected")
        else:
            st.write("**Mobile Friendly:** Viewport meta tag missing")

        # 6. Missing Alt Tags for Images
        images = soup.find_all('img')
        images_without_alt = [img['src'] for img in images if not img.get('alt')]
        st.write(f"**Images Missing Alt Text:** {len(images_without_alt)}")
        for img in images_without_alt:
            st.write(img)

        # 7. Sitemap & Robots.txt Check
        sitemap_url = urljoin(url, 'sitemap.xml')
        robots_url = urljoin(url, 'robots.txt')

        sitemap_status = requests.head(sitemap_url).status_code
        robots_status = requests.head(robots_url).status_code

        st.write(f"**Sitemap Status:** {'Found' if sitemap_status == 200 else 'Not Found'}")
        st.write(f"**Robots.txt Status:** {'Found' if robots_status == 200 else 'Not Found'}")

        # 8. Keyword Analysis with TF-IDF
        paragraphs = [p.get_text() for p in soup.find_all('p')]
        combined_text = ' '.join(paragraphs)

        if combined_text.strip():
            vectorizer = TfidfVectorizer(stop_words='english', max_features=10)
            tfidf_matrix = vectorizer.fit_transform([combined_text])
            keywords = vectorizer.get_feature_names_out()
            st.write("**Top Keywords (TF-IDF):**")
            for keyword in keywords:
                st.write(keyword)
        else:
            st.write("**No content found for TF-IDF analysis**")

        # Uptime Monitoring
        if uptime_check:
            st.write("**Uptime Monitoring Enabled - Checking site every 5 seconds**")
            while True:
                try:
                    uptime_response = requests.get(url, timeout=5)
                    st.write(f"Uptime Check: {uptime_response.status_code} - {time.strftime('%Y-%m-%d %H:%M:%S')}")
                except Exception as e:
                    st.write(f"Uptime Check Failed: {e}")
                time.sleep(5)

        # Email Alerts
        if email_alerts and recipient_email and len(broken_links) > 0:
            msg = MIMEText(f"Broken links detected on {url} - {broken_links}")
            msg['Subject'] = 'Website Monitoring Alert'
            msg['From'] = 'your_email@example.com'
            msg['To'] = recipient_email

            try:
                with smtplib.SMTP('smtp.gmail.com', 587) as server:
                    server.starttls()
                    server.login('your_email@example.com', 'your_password')
                    server.sendmail('your_email@example.com', recipient_email, msg.as_string())
                    st.write(f"**Email Alert Sent to {recipient_email}**")
            except Exception as e:
                st.write(f"**Failed to send email: {e}**")

    except Exception as e:
        st.write(f"An error occurred: {e}")

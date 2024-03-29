import psycopg2
from django.shortcuts import render
import pathlib
import textwrap
import google.generativeai as genai
from IPython.display import display
from IPython.display import Markdown
import os
from datetime import datetime


# from google.colab import userdata

def build_connection_with_database():
    conn = psycopg2.connect(database="news", host="localhost", port="5432", user="postgres",
                            password="Pukale@123")
    return conn


def close_connection_with_database(cur, conn):
    conn.commit()
    cur.close()
    conn.close()


def scrapper():
    import requests
    from bs4 import BeautifulSoup

    url = 'https://indianexpress.com/section/cities/mumbai/'

    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        div_element = soup.find('div', class_='north-east-grid explained-section-grid')

        if div_element:
            ul_element = div_element.find('ul')

            if ul_element:
                li_elements = ul_element.find_all('li')

                links = [li.find('h2').find('a').text.strip() for li in li_elements if li.find('h2')]

                return links
            else:
                print('No <ul> element found within the <div>')
        else:
            print('No <div> element found with the specified class or attributes')
    else:
        print(f'Failed to retrieve the webpage. Status code: {response.status_code}')


def gemini_api(headline):
    def to_markdown(text):
        text = text.replace('•', '  *')
        return Markdown(textwrap.indent(text, '> ', predicate=lambda _: True))

    os.environ['GOOGLE_API_KEY'] = 'AIzaSyCRnbt2sS3okoyl4IcAGeRcsyK3w0m8Sk8'
    # genai.configure(api_key="AIzaSyCRnbt2sS3okoyl4IcAGeRcsyK3w0m8Sk8")

    # Or use `os.getenv('GOOGLE_API_KEY')` to fetch an environment variable.
    # GOOGLE_API_KEY=userdata.get('GOOGLE_API_KEY')

    genai.configure(api_key=os.environ['GOOGLE_API_KEY'])

    model = genai.GenerativeModel('gemini-pro')

    # %%time
    response = model.generate_content(f"Generate a news on this headling '{headline}'")
    return response.text


def main_function():
    todays_date = datetime.now().date()
    links = scrapper()
    if not links:
        print('No links found.')
        return

    conn = build_connection_with_database()
    cur = conn.cursor()

    try:
        for link in links:
            current_time = datetime.now().time()
            cur.execute(f"SELECT COUNT(*) FROM data WHERE headline = '{link}'")
            count = cur.fetchone()[0]
            if count == 0:
                description = gemini_api(link)
                cur.execute(f"INSERT INTO data (headline, date, time, description) VALUES (%s, %s, %s, %s)",
                            (link, todays_date, current_time, description))

                # print(f"Inserted data for headline: {link}")
            else:
                pass
                # print(f"Data already exists for headline: {link}")
    except Exception as e:
        pass
        # print(f"Error: {e}")
    finally:
        close_connection_with_database(cur, conn)
        # print('Database connection closed


# main_function()


# Create your views here.
def home(request):
    todays_date = datetime.now().date()
    conn = build_connection_with_database()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM data WHERE date = '{todays_date}' ORDER BY time")
    data = cur.fetchall()
    context = {
        'news': data
    }
    return render(request, 'home.html', context=context)

from django.shortcuts import render
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
from selenium.webdriver.chrome.service import Service
import pandas as pd
from django.http import HttpResponse
from datetime import datetime
import re
import requests
from bs4 import BeautifulSoup

def search_view(request):
    if request.method == 'POST':
        location = request.POST.get('location')
        data = scrape_data(location)
        request.session['data'] = data  
        return render(request, 'result.html', {'businesses': data, 'location': location})
    return render(request, 'search.html')

def scrape_data(location):
    service = Service('D:/web scrape succes/chromedriver-win64/chromedriver.exe')  
    driver = webdriver.Chrome(service=service)
    
    driver.get('https://www.google.com/maps')
    time.sleep(10)  
    
    search_box = driver.find_element(By.ID, 'searchboxinput')
    search_box.send_keys(f'{location}')    
    search_box.send_keys(Keys.ENTER)
    time.sleep(10)  

    data = []
    businesses = driver.find_elements(By.CLASS_NAME, 'Nv2PK')

    for business in businesses:
        try:
            name = business.find_element(By.CLASS_NAME, 'qBF1Pd').text  
            address = business.find_element(By.XPATH, ".//div[@class='W4Efsd']/div[@class='W4Efsd'][1]").text  
            phone = 'Phone not available'
            phone_elements = business.find_elements(By.CLASS_NAME, 'UsdlK')
            if phone_elements:
                phone = phone_elements[0].text
            website = 'Website not available'
            website_buttons = business.find_elements(By.CLASS_NAME, 'lcr4fd')
            if website_buttons:
                website = website_buttons[-1].get_attribute('href')
            
            # Email, LinkedIn, Facebook, Instagram extraction
            email, linkedin, facebook, instagram = extract_social_media(website)
            
            data.append({
                'name': name,
                'address': address,
                'phone': phone,
                'website': website,
                'email': email,
                'linkedin': linkedin,
                'facebook': facebook,
                'instagram': instagram
            })
            
        except Exception as e:
            print(f"Error: {e}")
    
    driver.quit()
    return data

def extract_social_media(website):
    email = 'Email not available'
    linkedin = 'LinkedIn not available'
    facebook = 'Facebook not available'
    instagram = 'Instagram not available'
    
    # Fetch the website's content
    if website != 'Website not available':
        try:
            response = requests.get(website)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract email using regex
            email_match = re.search(r'[\w\.-]+@[\w\.-]+', response.text)
            if email_match:
                email = email_match.group(0)

            # Look for social media links
            for link in soup.find_all('a', href=True):
                href = link['href']
                if 'linkedin.com' in href:
                    linkedin = href
                elif 'facebook.com' in href:
                    facebook = href
                elif 'instagram.com' in href:
                    instagram = href

        except Exception as e:
            print(f"Error fetching website: {e}")
    
    return email, linkedin, facebook, instagram

def download_excel(request):
    data = request.session.get('data', [])
    df = pd.DataFrame(data)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f'google_maps_businesses_{timestamp}.xlsx'

    # Create the excel file as response
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = f'attachment; filename="{output_file}"'
    
    df.to_excel(response, index=False)
    return response

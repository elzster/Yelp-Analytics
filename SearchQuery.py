import json
import pandas as pd
import numpy as np
import requests
from config import api_key
print("Welcome to our Yelp Search Program!!!\nHere you can search many categories by city and state,\nAnd export the listings to a near CSV file.\nJust follow the Prompts!\n")
print("What type of Category would you like to search for? i.e Restaurant")
thing = input()
print("What city and state are you searching? i.e. New York City, NY")
location = input()
print("Offset Page Range? i.e. 50 results per page")
offset = int(input())

name = []
city = []
state = []
category = []
latitude = []
longitude = []
price = []
review_count = []
business_id = []
rating = []

def query_search(set_num):
    url = 'https://api.yelp.com/v3/businesses/search'
    headers = {
        'Authorization': 'Bearer {}'.format(api_key),}
    url_params = { #parameters passed to the API
    "term": thing,
    "location": location,
    'offset': offset_num,
     "limit":50
     }

    response = requests.get(url, headers=headers, params=url_params)
    return response.json()

for offset_num in range(offset):
    try:
        response = query_search(offset_num)
        businesses=response['businesses']
        for x in businesses:
            name.append(x['name'])
            business_id.append(x['id'])
            city.append(x['location']['city'])
            state.append(x['location']['state'])
            latitude.append(x['coordinates']['latitude'])
            longitude.append(x['coordinates']['longitude'])
            review_count.append(x['review_count'])
            rating.append(x['rating'])
            category.append(x['categories'][0]['title'])
            try:
                price.append(x['price'])
            except KeyError:
                price.append(0)
#             print(response)
    except AttributeError:
        print("error at ", offset_num)
    except KeyError:
        print("error at ", offset_num)

business_df = pd.DataFrame({
    "Business" : name,
    "Business ID": business_id,
    "City": city,
    "State": state,
    "Category": category,
    "Latitude": latitude,
    "Longitude": longitude,
    "Price":price,
    "Reviews": review_count,
    "Rating": rating
})
business_df

business_df.to_csv('data/'+(location)+'_'+(thing)+'.csv')

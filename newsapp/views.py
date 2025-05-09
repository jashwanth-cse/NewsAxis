from django.shortcuts import render
import requests
from django.http import JsonResponse
from urllib.parse import quote
import google.generativeai as genai
from .gemini_helper import summarize_with_gemini
from django.contrib.auth.decorators import login_required
import tweepy
from django.conf import settings
from django.core.cache import cache
from datetime import datetime, timedelta
import logging
from .models import CollegeTweet

api_key = 'pub_798075406aa4278718fe80e6f0e521c9a280b'
API_KEY = 'AIzaSyBI7oWgUcMOWD1JsuMvDRTUpNhZ0vW_apA'  # replace with your YouTube API key
CHANNEL_ID = 'UC77zVLSva6lRY6eqaDFUkuA'  # replace with Sri Eshwar College channel ID
# Configure your API key
countries = {
    "ae": "United Arab Emirates", "ar": "Argentina", "at": "Austria", "au": "Australia",
    "bd": "Bangladesh", "be": "Belgium", "bg": "Bulgaria", "br": "Brazil", "ca": "Canada",
    "ch": "Switzerland", "cn": "China", "cz": "Czech Republic", "de": "Germany",
    "eg": "Egypt", "es": "Spain", "fr": "France", "gb": "United Kingdom", "gr": "Greece",
    "hk": "Hong Kong", "hu": "Hungary", "id": "Indonesia", "ie": "Ireland", "il": "Israel",
    "in": "India", "it": "Italy", "jp": "Japan", "kr": "South Korea", "lt": "Lithuania",
    "lv": "Latvia", "mx": "Mexico", "my": "Malaysia", "ng": "Nigeria", "nl": "Netherlands",
    "no": "Norway", "nz": "New Zealand", "ph": "Philippines", "pk": "Pakistan", "pl": "Poland",
    "pt": "Portugal", "ro": "Romania", "rs": "Serbia", "ru": "Russia", "sa": "Saudi Arabia",
    "se": "Sweden", "sg": "Singapore", "th": "Thailand", "tr": "Turkey", "tw": "Taiwan",
    "ua": "Ukraine", "us": "United States", "ve": "Venezuela", "vn": "Vietnam", "za": "South Africa",
}
country_mapping = {
    "ae": "United Arab Emirates",
    "ar": "Argentina",
    "at": "Austria",
    "au": "Australia",
    "bd": "Bangladesh",
    "be": "Belgium",
    "bg": "Bulgaria",
    "br": "Brazil",
    "ca": "Canada",
    "ch": "Switzerland",
    "cn": "China",
    "cz": "Czech Republic",
    "de": "Germany",
    "eg": "Egypt",
    "es": "Spain",
    "fr": "France",
    "gb": "United Kingdom",
    "gr": "Greece",
    "hk": "Hong Kong",
    "hu": "Hungary",
    "id": "Indonesia",
    "ie": "Ireland",
    "il": "Israel",
    "in": "India",
    "it": "Italy",
    "jp": "Japan",
    "kr": "South Korea",
    "lt": "Lithuania",
    "lv": "Latvia",
    "mx": "Mexico",
    "my": "Malaysia",
    "ng": "Nigeria",
    "nl": "Netherlands",
    "no": "Norway",
    "nz": "New Zealand",
    "ph": "Philippines",
    "pk": "Pakistan",
    "pl": "Poland",
    "pt": "Portugal",
    "ro": "Romania",
    "rs": "Serbia",
    "ru": "Russia",
    "sa": "Saudi Arabia",
    "se": "Sweden",
    "sg": "Singapore",
    "th": "Thailand",
    "tr": "Turkey",
    "tw": "Taiwan",
    "ua": "Ukraine",
    "us": "United States",
    "ve": "Venezuela",
    "vn": "Vietnam",
    "za": "South Africa"
}



logger = logging.getLogger(__name__)

def college_news(request):
    cache_key = 'college_news_tweets'
    cache_timeout = 900  # 15 minutes

    # Check cache
    cached_news = cache.get(cache_key)
    latest_cached_time = None
    if cached_news:
        # Get the latest tweet's creation time from cache
        latest_cached_time = max(
            (datetime.strptime(item['created_at'], '%B %d, %Y %H:%M UTC') for item in cached_news),
            default=None
        )
        logger.info("Found cached college news")

    # Try fetching from Twitter API to check for newer posts
    try:
        logger.info("Fetching college news from Twitter API...")
        client = tweepy.Client(bearer_token=settings.TWITTER_BEARER_TOKEN)
        username = "srieshwar_cbe"

        # Get user ID
        user_response = client.get_user(username=username)
        if not user_response.data:
            logger.error(f"No user found for Twitter handle: {username}")
            return render(request, 'college_news.htm', {'news': cached_news or []})

        user_id = user_response.data.id

        # Fetch up to 10 tweets (increased to ensure we catch new ones)
        tweets_response = client.get_users_tweets(
            id=user_id,
            max_results=10,  # Increased to check for newer tweets
            tweet_fields=['created_at', 'text', 'attachments'],
            expansions=['attachments.media_keys'],
            media_fields=['url', 'type']
        )

        tweets = tweets_response.data or []
        includes = tweets_response.includes if hasattr(tweets_response, 'includes') else {}

        # Build media dictionary for images
        media_dict = {}
        if 'media' in includes:
            for media in includes['media']:
                if media.type == 'photo' and hasattr(media, 'url'):
                    media_dict[media.media_key] = media.url

        news = []
        for tweet in tweets:
            # Skip if tweet is older than latest cached tweet (if cache exists)
            tweet_time = tweet.created_at
            if latest_cached_time and tweet_time <= latest_cached_time:
                continue

            image_url = None
            if hasattr(tweet, 'attachments') and 'media_keys' in tweet.attachments:
                media_key = tweet.attachments['media_keys'][0]
                image_url = media_dict.get(media_key)

            tweet_url = f"https://x.com/{username}/status/{tweet.id}"
            created_at_str = tweet.created_at.strftime('%B %d, %Y %H:%M UTC') if tweet.created_at else "Unknown"

            news_item = {
                'id': str(tweet.id),
                'title': tweet.text[:50] + '...' if len(tweet.text) > 50 else tweet.text,
                'text': tweet.text,
                'image': image_url,
                'created_at': created_at_str,
                'url': tweet_url
            }
            news.append(news_item)

            # Save to DB
            CollegeTweet.objects.update_or_create(
                tweet_id=str(tweet.id),
                defaults={
                    'text': tweet.text,
                    'image': image_url,
                    'created_at': tweet.created_at,
                    'url': tweet_url
                }
            )

        # If new tweets found, combine with cached or DB tweets
        if news:
            # Fetch recent DB tweets to fill up to 10 items
            db_tweets = CollegeTweet.objects.all().order_by('-created_at')[:10]
            db_news = [
                {
                    'id': tweet.tweet_id,
                    'title': tweet.text[:50] + '...' if len(tweet.text) > 50 else tweet.text,
                    'text': tweet.text,
                    'image': tweet.image,
                    'created_at': tweet.created_at.strftime('%B %d, %Y %H:%M UTC'),
                    'url': tweet.url
                } for tweet in db_tweets
            ]

            # Combine new and DB tweets, remove duplicates, sort by created_at
            all_news = news + [item for item in db_news if item['id'] not in {n['id'] for n in news}]
            all_news.sort(key=lambda x: datetime.strptime(x['created_at'], '%B %d, %Y %H:%M UTC'), reverse=True)
            news = all_news[:10]

            # Update cache
            cache.set(cache_key, news, cache_timeout)
            logger.info(f"Fetched and cached {len(news)} tweet(s) from Twitter")
            return render(request, 'college_news.htm', {'news': news})

    except tweepy.TooManyRequests as e:
        logger.warning(f"Twitter API rate limit exceeded: {str(e)}")
    except Exception as e:
        logger.error(f"Error fetching from Twitter: {str(e)}")

    # Fallback to database if API fails
    try:
        db_tweets = CollegeTweet.objects.all().order_by('-created_at')[:10]
        if db_tweets.exists():
            news = [
                {
                    'id': tweet.tweet_id,
                    'title': tweet.text[:50] + '...' if len(tweet.text) > 50 else tweet.text,
                    'text': tweet.text,
                    'image': tweet.image,
                    'created_at': tweet.created_at.strftime('%B %d, %Y %H:%M UTC'),
                    'url': tweet.url
                } for tweet in db_tweets
            ]
            cache.set(cache_key, news, cache_timeout)
            logger.info("Serving college news from database")
            return render(request, 'college_news.htm', {'news': news})
    except Exception as e:
        logger.error(f"Error querying database: {str(e)}")

    # Fallback to cached news or empty list
    logger.info("Serving cached or empty news")
    return render(request, 'college_news.htm', {'news': cached_news or []})
from django.http import JsonResponse

from django.http import JsonResponse
from .models import CollegeTweet

def college_news_json(request):
    tweets = CollegeTweet.objects.all().order_by('-created_at')[:5]
    data = [
        {
            "text": tweet.text,
            "created_at": tweet.created_at.strftime('%B %d, %Y %H:%M UTC')
        }
        for tweet in tweets
    ]
    return JsonResponse(data, safe=False)

def home_view(request):
    return render(request, 'home.htm')
def category_news(request, category_name):
    import requests

    url = f'https://newsdata.io/api/1/news?apikey={api_key}&language=en&category={category_name}'

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        category_news = []
        seen_titles = set()

        if data.get('results'):
            for article in data['results']:
                title = (article.get('title') or '').strip()
                link = article.get('link')
                description = (article.get('description') or '').strip()
                image = article.get('image_url')

                # Filter out duplicates and incomplete entries
                if (
                    title and title not in seen_titles and
                    description and link
                ):
                    seen_titles.add(title)

                    # Fallback image if missing
                    if not image:
                        image = 'https://via.placeholder.com/400x200.png?text=No+Image'

                    category_news.append({
                        'title': title,
                        'description': description,
                        'url': link,
                        'image': image
                    })

                if len(category_news) == 10:
                    break
        else:
            category_news = [{
                'title': 'No news found',
                'description': 'No articles available at the moment.',
                'url': '#',
                'image': 'https://via.placeholder.com/400x200.png?text=No+Image'
            }]

    except requests.exceptions.RequestException as e:
        category_news = [{
            'title': 'Error fetching news',
            'description': str(e),
            'url': '#',
            'image': 'https://via.placeholder.com/400x200.png?text=No+Image'
        }]

    return render(request, 'category_news.htm', {
        'category_news': category_news,
        'selected_category': category_name
    })


# views.py
def home(request):
    url = f'https://newsdata.io/api/1/news?apikey={api_key}&language=en&country=in,us,gb'

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        trending_news = []
        seen_titles = set()
        seen_links = set()

        if isinstance(data.get('results'), list):
            for article in data['results']:
                title = (article.get('title') or '').strip()
                link = article.get('link')
                description = (article.get('description') or '').strip()
                image = article.get('image_url') or 'https://via.placeholder.com/800x400.png?text=No+Image'

                if title and link and title not in seen_titles and link not in seen_links:
                    seen_titles.add(title)
                    seen_links.add(link)

                    trending_news.append({
                        'title': title,
                        'description': description or 'No description available',
                        'url': link,
                        'image': image
                    })

                if len(trending_news) == 6:
                    break
        else:
            trending_news = []

    except requests.exceptions.RequestException as e:
        trending_news = []

    return render(request, 'home.htm', {'trending_news': trending_news})
import requests
from django.shortcuts import render

import requests
from urllib.parse import quote
from django.shortcuts import render

def nearby_news(request):
    lat = request.GET.get('lat')
    lon = request.GET.get('lon')
    city = None
    news = []

    if lat and lon:
        try:
            geo_url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
            response = requests.get(geo_url, headers={'User-Agent': 'NewsAxis'})
            data = response.json()
            city = data.get('address', {}).get('city') or data.get('address', {}).get('town') or data.get('address', {}).get('state')

            if city:
                api_key = 'c45f7b36df33f364c1ccd06b3b641e63'
                city_encoded = quote(city)
                news_url = f"https://gnews.io/api/v4/search?q={city_encoded}&lang=en&country=in&apikey={api_key}"

                news_response = requests.get(news_url)

                if news_response.status_code == 200:
                    news = news_response.json().get('articles', [])
        except Exception as e:
            print("Error getting nearby news:", e)

    return render(request, 'nearby_news.htm', {
        'news': news,
        'city': city,
        'lat': lat,
        'lon': lon
    })
def auth_view(request):
    return render(request, 'auth.htm')
def country_list(request):
    return render(request, 'country_list.htm', {'countries': countries})

import requests
from django.http import JsonResponse
def user_articles(request):
    return render(request, 'user_articles.htm')
def general_news_json(request):
    url = f"https://newsdata.io/api/1/news?apikey={api_key}&language=en&country=in&category=top"

    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            articles = data.get('results', [])
            news = [
                {
                    'title': article.get('title', 'No Title'),
                    'link': article.get('link', '')
                }
                for article in articles[:5]  # Limit to 5 headlines
            ]
            return JsonResponse(news, safe=False)
        else:
            return JsonResponse([], safe=False)
    except Exception as e:
        print(f"Error fetching general news: {str(e)}")
        return JsonResponse([], safe=False)
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Article
from .forms import ArticleForm
from django.conf import settings
import os

def terms_view(request):
    return render(request, 'terms.htm')
def bookmarks(request):
    return render(request, 'bookmarks.htm')
def country_news(request, country_code):
    url = f"https://newsdata.io/api/1/news?apikey={api_key}&country={country_code}&language=en"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        articles = []
        seen_links = set()

        for article in data.get('results', []):
            link = article.get('link')
            if link and link not in seen_links:
                seen_links.add(link)
                articles.append({
                    'title': article.get('title', 'No Title'),
                    'description': article.get('description', 'No description available'),
                    'link': link,
                    'image': article.get('image_url') or 'https://via.placeholder.com/400x200.png?text=No+Image'
                })

    except requests.exceptions.RequestException as e:
        articles = [{
            'title': 'Error fetching news',
            'description': str(e),
            'link': '#',
            'image': 'https://via.placeholder.com/400x200.png?text=No+Image'
        }]

    country_name = country_mapping.get(country_code.lower(), "Unknown Country")
    return render(request, 'country_news.htm', {
        'articles': articles,
        'country_name': country_name
    })
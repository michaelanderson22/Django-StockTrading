from django.shortcuts import render
from .models import Stock
from django.conf import settings
from django.utils import timezone
import requests
from requests.exceptions import HTTPError


# Create your views here.

def HomePage(request):
    api_key = settings.ALPHA_VANTAGE_API_KEY
    symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'GOOGL', 'NVDA', 'META', 'TSLA', 'LLY', 'TSM', 'WMT', 'JNJ', 'ORCL', 'HD', 'ADBE', 'COST', 'KO', 'TM', 'BAC', 'PEP']  # Add more stock symbols as needed

    for symbol in symbols:
        try:
            # Check the last update timestamp for the stock
            last_update_time = Stock.objects.filter(symbol=symbol).order_by('-last_updated').first()

            # Only make an API call if it's been more than a day since the last update or no previous update exists
            if not last_update_time or (timezone.now() - last_update_time.last_updated).days > 0:
                url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={api_key}'
                response = requests.get(url)
                response.raise_for_status()  # Raise an exception for bad responses

                data = response.json()
                time_series = data.get('Time Series (Daily)', {})

                for date, info in time_series.items():
                    # Check if a record with the same symbol and date already exists
                    existing_stock = Stock.objects.filter(symbol=symbol, last_updated=date).first()

                    if existing_stock:
                        # Update existing record
                        existing_stock.current_price = float(info['1. price'])
                        existing_stock.change_percent = float(info['2. change percent'])
                        existing_stock.last_updated = date
                        existing_stock.save()
                    else:
                        # Create a new record
                        stock = Stock(
                            symbol=symbol,
                            current_price=float(info['1. price']),
                            change_percent=float(info['2. change percent']),
                            last_updated=date,
                        )
                        stock.save()

        except HTTPError as e:
            print(f"Error fetching data for {symbol}: {e}")

    stocks = Stock.objects.all()

    return render(request, 'homepage.html', {'stocks': stocks})


def AddFunds(request):
    context = {}
    return render(request, 'addfunds.html')


def UserPortfolio(request):
    context = {}
    return render(request, 'userportfolio.html')

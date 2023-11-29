from django.shortcuts import render, redirect
from .models import *
from django.conf import settings
from django.utils import timezone
import requests
from requests.exceptions import HTTPError
from .forms import AddFundsForm
from datetime import datetime


# Create your views here.

def HomePage(request):
    user_profile = UserProfile.objects.get(user=request.user)
    funds = user_profile.funds

    api_key = settings.ALPHA_VANTAGE_API_KEY
    symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'GOOGL', 'NVDA', 'META', 'TSLA', 'LLY', 'TSM', 'WMT', 'JNJ', 'ORCL',
               'HD', 'ADBE', 'COST', 'KO', 'TM', 'BAC', 'PEP']  # Add more stock symbols as needed

    for symbol in symbols:
        try:
            # Check the last update timestamp for the stock
            last_update_time = Stock.objects.filter(symbol=symbol).order_by('-last_updated').first()

            # Only make an API call if it's been more than two days since the last update and you have responses left
            if last_update_time and (timezone.now() - last_update_time.last_updated).days > 1:
                print((timezone.now() - last_update_time.last_updated).days)

                url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}'
                response = requests.get(url)
                response.raise_for_status()  # Raise an exception for bad responses

                data = response.json()
                print(data)
                time_series = data.get('Global Quote', {})

                # Check if a record with the same symbol already exists
                existing_stock = Stock.objects.filter(symbol=symbol).first()

                # Check if it's been more than two days since the last update
                if existing_stock and (timezone.now() - existing_stock.last_updated).days > 1:
                    # Update existing record
                    existing_stock.current_price = float(time_series.get('05. price', 0))
                    existing_stock.change_percent = time_series.get('10. change percent', '0%')
                    # Default to '0%' if not provided
                    existing_stock.last_updated = timezone.now()
                    existing_stock.save()
                elif not existing_stock:
                    # Create a new record
                    stock = Stock(
                        symbol=symbol,
                        current_price=float(time_series.get('05. price', 0)),
                        change_percent=time_series.get('10. change percent', '0%'),
                        # Default to '0%' if not provided
                        last_updated=timezone.now(),
                    )
                    stock.save()

        except HTTPError as e:
            print(f"Error fetching data for {symbol}: {e}")

    stocks = Stock.objects.all()

    return render(request, 'homepage.html', {'stocks': stocks, 'funds': funds})


def AddFunds(request):
    user_profile = UserProfile.objects.get(user=request.user)

    if request.method == 'POST':
        form = AddFundsForm(request.POST)
        if form.is_valid():
            # Update the user's funds
            amount = form.cleaned_data['amount']
            user_profile.funds += amount
            user_profile.save()
            return redirect('mysite:User Portfolio')
    else:
        form = AddFundsForm()

    return render(request, 'addfunds.html', {'form': form})


def UserPortfolio(request):
    user_profile = UserProfile.objects.get(user=request.user)
    funds = user_profile.funds

    return render(request, 'userportfolio.html', {'funds': funds})

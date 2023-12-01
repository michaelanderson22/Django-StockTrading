from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import *
from django.conf import settings
from django.utils import timezone
import requests
from requests.exceptions import HTTPError
from .forms import AddFundsForm, StockTransactionForm
from decimal import Decimal
from datetime import datetime
from django.shortcuts import get_object_or_404
from django.contrib import messages


# Create your views here.

def HomePage(request):
    funds = 0  # For anonymous user

    if request.user.is_authenticated:
        user_profile = UserProfile.objects.get(user=request.user)
        funds = user_profile.funds

    api_key = settings.ALPHA_VANTAGE_API_KEY
    symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'GOOGL', 'NVDA', 'META', 'TSLA', 'LLY', 'TSM', 'WMT', 'JNJ', 'ORCL',
               'HD', 'ADBE', 'COST', 'KO', 'TM', 'BAC', 'PEP']  # Add more stock symbols as needed

    for symbol in symbols:
        try:
            # Check the last update timestamp for the stock
            last_update_time = Stock.objects.filter(symbol=symbol).order_by('-last_updated').first()
            last_update_time = 0

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
    stock_forms = [StockTransactionForm(prefix=str(stock.id)) for stock in stocks]
    stocks_and_forms = zip(stocks, stock_forms)

    return render(request, 'homepage.html', {'stocks': stocks, 'funds': funds, 'stocks_and_forms': stocks_and_forms})


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

    # Fetch the user's stock portfolio directly
    stock_portfolio = StockPortfolio.objects.get(user=user_profile.user)

    # Fetch the portfolio stocks related to the user's stock portfolio
    portfolio_stocks = PortfolioStock.objects.filter(portfolio=stock_portfolio)

    # Calculate the value of each stock and add it to the portfolio_stocks queryset
    for stock in portfolio_stocks:
        stock.value = stock.quantity * stock.stock.current_price

    stock_forms = [StockTransactionForm(prefix=str(stock.id)) for stock in portfolio_stocks]
    stocks_and_forms = zip(portfolio_stocks, stock_forms)

    return render(request, 'userportfolio.html',
                  {'funds': funds, 'user_stocks': portfolio_stocks, 'stocks_and_forms': stocks_and_forms})


def calculate_total_cost(price, quantity):
    return Decimal(price) * Decimal(quantity)


def buy_stock(request, stock_symbol):
    stock = Stock.objects.get(symbol=stock_symbol)
    user_profile = UserProfile.objects.get(user=request.user)
    stock_portfolio = StockPortfolio.objects.get(user=user_profile.user)

    if request.method == 'POST':
        form = StockTransactionForm(request.POST, prefix=str(stock.id))
        if form.is_valid():
            quantity = form.cleaned_data['quantity']

            # Calculate the cost of the stocks and update funds
            total_cost = calculate_total_cost(stock.current_price, quantity)

            if user_profile.funds >= total_cost:
                # Get or create the PortfolioStock entry with the initial quantity
                portfolio_stock, created = PortfolioStock.objects.get_or_create(
                    portfolio=stock_portfolio, stock=stock,
                    defaults={'quantity': quantity}
                )

                if not created:
                    # If the portfolio stock already exists, update the quantity
                    portfolio_stock.quantity += quantity
                    portfolio_stock.save()

                user_profile.funds -= total_cost
                user_profile.save()

                # Redirect user to their portfolio if the purchase is successful.
                return redirect('mysite:User Portfolio')
            else:
                messages.error(request, 'Insufficient Funds.')
                form.add_error('quantity', 'Insufficient funds.')

    else:
        form = StockTransactionForm()

    # If the form is not valid or it's a GET request, render the template with the form
    return redirect('mysite:Home Page')


@login_required
def sell_stock(request, stock_symbol):
    user_profile = UserProfile.objects.get(user=request.user)

    # Fetch the user's stock portfolio directly
    stock_portfolio = StockPortfolio.objects.get(user=user_profile.user)

    # Fetch the specific portfolio stock related to the user's stock portfolio and the given stock symbol
    portfolio_stock = get_object_or_404(PortfolioStock, portfolio=stock_portfolio, stock__symbol=stock_symbol)

    if request.method == 'POST':
        form = StockTransactionForm(request.POST, prefix=str(portfolio_stock.id))
        if form.is_valid():
            quantity = form.cleaned_data['quantity']

            # Calculate the value of the stocks and update funds
            total_value = calculate_total_cost(portfolio_stock.stock.current_price, quantity)

            if portfolio_stock.quantity >= quantity:
                # Reduce the quantity of the stock
                portfolio_stock.quantity -= quantity
                portfolio_stock.save()

                # Update user funds
                user_profile.funds += total_value
                user_profile.save()

                # Remove the stock from the portfolio if its quantity reaches zero
                if portfolio_stock.quantity == 0:
                    portfolio_stock.delete()

                # Redirect user to their portfolio if the sale is successful.
                return redirect('mysite:User Portfolio')
            else:
                messages.error(request, 'Insufficient Shares.')
                form.add_error('quantity', 'Insufficient Shares.')
    else:
        form = StockTransactionForm()

    # If the form is not valid or it's a GET request, render the template with the form
    return redirect('mysite:User Portfolio')

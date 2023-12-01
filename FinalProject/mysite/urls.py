from . import views
from django.urls import path

app_name = 'mysite'
urlpatterns = [
    path('', views.HomePage, name="Home Page"),
    path('funds/', views.AddFunds, name="Funds Page"),
    path('userportfolio/', views.UserPortfolio, name="User Portfolio"),
    path('buy_stock/<str:stock_symbol>/', views.buy_stock, name='buy_stock'),
    path('sell_stock/<str:stock_symbol>/', views.sell_stock, name="sell_stock"),
]
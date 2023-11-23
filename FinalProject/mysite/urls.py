from . import views
from django.urls import path

app_name = 'mysite'
urlpatterns = [
    path('', views.HomePage, name="Home Page"),
    path('funds/', views.AddFunds, name="Funds Page"),
    path('userportfolio/', views.UserPortfolio, name="User Portfolio")
]
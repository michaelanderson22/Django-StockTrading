from django.shortcuts import render


# Create your views here.

def HomePage(request):
    context = {}
    return render(request, 'homepage.html')


def AddFunds(request):
    context = {}
    return render(request, 'addfunds.html')


def UserPortfolio(request):
    context = {}
    return render(request, 'userportfolio.html')

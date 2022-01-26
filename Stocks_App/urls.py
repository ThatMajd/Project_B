
from django.urls import path
from Stocks_App import views

urlpatterns = [
    path('', views.home, name='home'),
    path('query_results', views.query_results, name='query_results'),
    path('transactions', views.transactions, name='transactions'),
    path('buy_stocks', views.buy_stocks, name='buy_stocks')
]
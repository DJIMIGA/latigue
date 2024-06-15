from django.shortcuts import render

from django.http import HttpResponse

from django.shortcuts import render

from portfolio.models import Portfolio


# Create your views here.
def portfolio_index(request):
    portfolios = Portfolio.objects.all()
    context = {"portfolios": portfolios}
    return render(request, "portfolio_index.html", context)



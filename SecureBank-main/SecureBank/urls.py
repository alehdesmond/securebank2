"""
URL configuration for SecureBank project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.views.generic import RedirectView
from backend.banking import views as banking_views  # Import banking views
from . import views

def home_view(request):
    if request.user.is_authenticated:
        return redirect('banking:dashboard')
    return redirect('accounts:login')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),
    path('dashboard/', login_required(lambda request: redirect('banking:dashboard')), name='dashboard'),
    path('accounts/', include('backend.accounts.urls')),
    path('banking/', include(('backend.banking.urls', 'banking'), namespace='banking')),
    path('manager/dashboard/', banking_views.manager_dashboard, name='manager_dashboard'),
    path('manager/approve_account/<uuid:account_id>/', banking_views.approve_account, name='approve_account'),
    path('manager/deny_account/<uuid:account_id>/', banking_views.deny_account, name='deny_account'),
    
]

# Custom error handlers
handler404 = 'SecureBank.views.custom_404'
handler500 = 'SecureBank.views.custom_500'
handler403 = 'SecureBank.views.custom_403'






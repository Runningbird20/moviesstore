from django.shortcuts import render
from django.contrib.auth import login as auth_login, authenticate, logout as auth_logout
from django.shortcuts import redirect
from .forms import CustomUserCreationForm, CustomErrorList
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from cart.models import Order, Item

@login_required
def logout(request):
    auth_logout(request)
    return redirect('home.index')

def login(request):
    template_data = {}
    template_data['title'] = 'Login'

    if request.method == 'GET':
        return render(request, 'accounts/login.html', {'template_data': template_data})
    
    elif request.method == 'POST':
        user = authenticate(request, username = request.POST['username'], password = request.POST['password'])
    
    if user is None:
        template_data['error'] = 'The username or password is incorrect.'
        return render(request, 'accounts/login.html', {'template_data': template_data})

    else:
        auth_login(request, user)
        return redirect('home.index')

def signup(request):
    template_data = {}
    template_data['title'] = 'Sign Up'

    if request.method == 'GET':
        template_data['form'] = CustomUserCreationForm()
        return render(request, 'accounts/signup.html', {'template_data': template_data})
    
    elif request.method == 'POST':
        form = CustomUserCreationForm(request.POST, error_class=CustomErrorList)

        if form.is_valid():
            form.save()
            return redirect('accounts.login')
        
        else:
            template_data['form'] = form
            return render(request, 'accounts/signup.html', {'template_data': template_data})

@login_required
def orders(request):
    template_data = {}
    template_data['title'] = 'Orders'
    template_data['orders'] = request.user.order_set.all
    return render(request, 'accounts/order.html', {'template_data': template_data})

@login_required
def most_purchases(request):
    if request.user.is_superuser:
        template_data = {}
        purchases_by_user = {}
        for item in Item.objects.all():
            user = item.order.user
            quantity = item.quantity

            if (not user in purchases_by_user):
                purchases_by_user[user] = 0
            purchases_by_user[user] += quantity

        sorted_dict = {}
        for key in sorted(purchases_by_user, key=purchases_by_user.get):
            sorted_dict[key] = purchases_by_user[key]

        most_user = list(sorted_dict)[-1]
        most_quantity = sorted_dict[most_user]
        
        template_data['user'] = most_user
        template_data['quantity'] = most_quantity
        return render(request, 'accounts/most_purchases.html', {'template_data': template_data})

    else:
        return redirect('home.index')

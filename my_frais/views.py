from django.db import IntegrityError
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.contrib.auth import login as login_django, authenticate, logout as logout_django
from django.contrib.auth.models import AbstractUser, User, AnonymousUser
from django.contrib.auth.decorators import login_required


from my_frais.models import Account

# Create your views here.
def index(request: HttpRequest) -> HttpResponse:
    return render(request, 'index.html')

def logout(request: HttpRequest) -> HttpResponse | JsonResponse:
    logout_django(request)
    return index(request)

def login(request: HttpRequest) -> HttpResponse | JsonResponse:
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user:AbstractUser | None = authenticate(request, username=username, password=password)
        if user:
            login_django(request=request, user=user)
            return JsonResponse(
                {
                    'message':'Connexion réussie'
                },
                status=200
            )
        else:
            return JsonResponse(
                {
                    'message':'Veuillez vérifier vos informations de connexion'
                },
                status=401
            )
    return render(request, 'login.html')

def register(request: HttpRequest) -> HttpResponse | JsonResponse:
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        try:
            user:User = User.objects.create_user(
                username=str(username),
                email=email,
                password=password
            )
            if user:
                login_django(request, user)
                return JsonResponse(
                    {'message': "Inscription réussie"},
                    status=201
                )
        except IntegrityError as ie:
            print(f"Erreur d'intégrity : {ie}")
            return JsonResponse(
                {'message': "Nom d'utilisateur ou email déjà utilisé."},
                status=409
            )
        except ValueError as ve:
            print(f"Erreur value error : {ve}")
            return JsonResponse(
                {'message': "Erreur dans les données du formulaire."},
                status=400
            )
    return render(request, 'register.html')

@login_required
def my_accounts(request: HttpRequest) -> HttpResponse:
    user = request.user
    accounts = Account.objects.filter(user=user)
    return render(request, 'my_accounts.html', context={'accounts':accounts})
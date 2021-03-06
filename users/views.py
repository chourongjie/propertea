from django.contrib.auth import authenticate, login, logout
from django.contrib.sites.shortcuts import get_current_site
from django.template.defaultfilters import striptags
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from .models import User
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from .forms import SignUpForm

# Create your views here.
from .tokens import account_activation_token


def index(request):
    if not request.user.is_authenticated:
        return render(request, "users/login.html", {"message": None})
    context = {
        "user": request.user
    }
    return render(request, "users/user.html", context)


def login_view(request):
    username = request.POST["username"]
    password = request.POST["password"]
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        messages.error(request, "Invalid Credentials")
        return render(request, "users/login.html")


def logout_view(request):
    logout(request)
    messages.success(request, "Logged Out.")
    return render(request, "users/login.html")


def createaccount_view(request):
    form = SignUpForm(request.POST)
    if form.is_valid():
        form.save()
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password1')
        user = authenticate(username=username, password=password)

        # user can't login until link confirmed
        user.is_active = False
        user.save()
        current_site = get_current_site(request)
        subject = 'Please Activate Your Account'
        # load a template like get_template()
        # and calls its render() method immediately.
        message = render_to_string('users/activation_request.html', {
            'user': user,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            # method will generate a hash value with user related data
            'token': account_activation_token.make_token(user),
        })
        user.email_user(subject, message)
        return redirect("activation_sent")
    else:
        if striptags(form.errors) != "usernameThis field is required.emailThis field is required.first_nameThis field " \
                                     "is required.last_nameThis field is required.password1This field is " \
                                     "required.password2This field is required.":
            errorlist = []
            for errors in form.errors.items():
                errorlist.append(errors[1][0])
            messages.error(request, errorlist)
            print(errorlist)
        form = SignUpForm()
    return render(request, 'users/createaccount.html', {'form': form})


def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    # checking if the user exists, if the token is valid.
    if user is not None and account_activation_token.check_token(user, token):
        # if valid set active true
        user.is_active = True
        # set signup_confirmation true
        user.profile.signup_confirmation = True
        user.save()
        login(request, user)
        return redirect('index')
    else:
        return render(request, 'users/activation_invalid.html')


def activation_sent_view(request):
    return render(request, 'users/activation_sent.html')

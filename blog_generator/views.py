import logging
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

# Create your views here.


def index(request):
    return render(request, "index.html")


def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("/")
        else:
            return render(
                request,
                "login.html",
                {
                    "error_message": "로그인에 실패했습니다. 사용자 이름과 비밀번호를 확인하세요."
                },
            )
    return render(request, "login.html")


def user_signup(request):
    try:
        if request.method != "POST":
            return render(request, "signup.html")

        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        repeat_password = request.POST.get("repeat_password")

        # validate
        if not username:
            raise ValueError("사용자 이름을 입력해주세요.")
        if not email:
            raise ValueError("이메일을 입력해주세요.")
        if not password:
            raise ValueError("비밀번호를 입력해주세요.")
        if not repeat_password:
            raise ValueError("비밀번호 확인을 입력해주세요.")

        if password != repeat_password:
            raise ValueError("비밀번호가 일치하지 않습니다.")

        if User.objects.filter(username=username).exists():
            raise ValueError("이미 존재하는 사용자 이름입니다.")
        if User.objects.filter(email=email).exists():
            raise ValueError("이미 존재하는 이메일입니다.")

        # User 생성
        user = User.objects.create_user(
            username=username, email=email, password=password
        )
        user.save()
        login(request, user)
        return redirect("/")

    except ValueError as ve:
        return render(request, "signup.html", {"error_message": str(ve)})
    except Exception as e:
        logging.error(str(e))
        return render(
            request,
            "signup.html",
            {"error_message": "회원가입에 실패했습니다. 다시 시도해주세요."},
        )


@login_required
def user_logout(request):
    logout(request)
    return redirect("/")

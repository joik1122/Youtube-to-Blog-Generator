from decouple import config
import json
import logging
import os
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
from pytube import YouTube
import assemblyai as aai
import openai

# Create your views here.


@login_required
def index(request):
    return render(request, "index.html")


@csrf_exempt  # csrf 토큰을 사용하지 않도록 설정
def generate_blog(request):
    if request.method == "POST":
        youtube_link = None
        try:
            data = json.loads(request.body)
            youtube_link = data.get("link")
        except (KeyError, json.JSONDecodeError) as e:
            logging.error(str(e))
            return JsonResponse(
                {"error": "Invalid data sent"},
                status=400,
            )
        # get youtube title
        title = get_youtube_title(youtube_link)
        # get transcript
        transcription = get_transcription(youtube_link)
        if not transcription:
            return JsonResponse(
                {"error": "Failed to get transcription from the video"},
                status=500,
            )

        # use OpenAI to getnerate the blog
        blog_content = generate_blog_from_transcription(transcription)
        if not blog_content:
            return JsonResponse(
                {"error": "Failed to generate blog content"}, status=500
            )

        # save blog article to database

        # return blog article as a response
        return JsonResponse({"content": blog_content})
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)


def get_youtube_title(youtube_link):
    return YouTube(youtube_link).title


def download_audio(link):
    yt = YouTube(link)
    video = yt.streams.filter(only_audio=True).first().download()
    out_file = video.download(output_path=settings.MEDIA_ROOT)
    base, ext = os.path.splitext(out_file)
    new_file = base + ".mp3"
    os.rename(out_file, new_file)
    return new_file


def get_transcription(youtube_link):
    audio_file = download_audio(youtube_link)
    aai.settings.api_key = config("ASSEMBLYAI_API_KEY")
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(audio_file)

    return transcript.text


def generate_blog_from_transcription(transcription):
    openai.api_key = config("OPENAI_API_KEY")
    prompt = f"Based on the following transcription from a Youtube video, write a comprehensive blog article, write it based on the transcript, but dont make it look like a youtube video, make it look like a proper blog article\n\n{transcription}\n\nArticle:"

    response = openai.completions.create(
        model="text-davinci-003",
        prompt=prompt,
        max_tokens=1000,
    )

    return response.choices[0].text.strip()


def user_login(request):
    if request.method == "POST":
        try:
            username = request.POST.get("username")
            password = request.POST.get("password")
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("/")
            else:
                raise Exception("사용자 이름 또는 비밀번호가 일치하지 않습니다.")
        except Exception as e:
            logging.error(str(e))
            return render(
                request,
                "login.html",
                {"error_message": str("로그인에 실패했습니다. " + str(e))},
            )
    return render(request, "login.html")


def user_signup(request):
    try:
        if request.method != "POST":
            return render(request, "signup.html")

        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        repeat_password = request.POST.get("repeatPassword")

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

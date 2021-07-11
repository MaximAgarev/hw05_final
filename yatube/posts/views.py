from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_GET, require_http_methods

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User


@cache_page(20, key_prefix='index_page')
@require_GET
def index(request):
    all_posts = Post.objects.all()

    paginator = Paginator(all_posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)

    return render(request, "index.html", {"page": page})


@require_GET
def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    all_posts = group.posts.all()

    paginator = Paginator(all_posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)

    return render(request, "posts/group.html", {"group": group, "page": page})


@require_GET
def profile(request, username):
    user_profile = get_object_or_404(User, username=username)
    all_posts = user_profile.posts.all()

    paginator = Paginator(all_posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    following = request.user.is_authenticated and Follow.objects.filter(
        user=request.user,
        author=user_profile
    ).exists()

    return render(
        request,
        "posts/profile.html",
        {"user_profile": user_profile, "page": page, "following": following}
    )


@require_GET
def post_view(request, username, post_id):
    user_profile = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, id=post_id, author=user_profile.id)

    form = CommentForm()
    comments = Comment.objects.filter(post_id=post_id)

    return render(
        request,
        "posts/post.html",
        {
            "user_profile": user_profile,
            "post": post,
            "form": form,
            "comments": comments,
        },
    )


@require_http_methods(["GET", "POST"])
@login_required
def new_post(request):
    form = PostForm(request.POST or None, request.FILES or None)

    if not form.is_valid():
        return render(request, "posts/new.html", {"form": form})

    post = form.save(commit=False)
    post.author = request.user
    post.save()

    return redirect("/")


@require_http_methods(["GET", "POST"])
@login_required
def post_edit(request, username, post_id):
    user_profile = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, id=post_id, author=user_profile.id)

    if request.user.username != username:
        return redirect("post", username, post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )

    if form.is_valid():
        form.save()
        return redirect("post", username, post_id)

    return render(
        request, "posts/new.html", {
            "form": form,
            "post_id": post_id,
            "editing": True
        }
    )


@require_http_methods(["GET", "POST"])
@login_required
def add_comment(request, username, post_id):
    form = CommentForm(request.POST or None)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.post_id = post_id
        comment.author = request.user
        comment.save()
    return redirect("post", username, post_id)


@login_required()
def follow_index(request):
    follow_posts = Post.objects.filter(author__following__user=request.user)

    paginator = Paginator(follow_posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)

    return render(request, "posts/follow.html", {"page": page})


@login_required()
def profile_follow(request, username):
    user_profile = get_object_or_404(User, username=username)
    if not user_profile == request.user:
        if not Follow.objects.filter(
                user=request.user,
                author=user_profile
        ).exists():
            Follow.objects.create(
                user=request.user,
                author=user_profile
            )
            return profile(request, username)
    return profile(request, username)


@login_required()
def profile_unfollow(request, username):
    user_profile = get_object_or_404(User, username=username)
    Follow.objects.filter(
        user=request.user,
        author=user_profile
    ).delete()
    return profile(request, username)


def page_not_found(request, exception=None):
    return render(request, "misc/404.html",
                  {"path": request.path}, status=404)


def server_error(request):
    return render(request, "misc/500.html", status=500)

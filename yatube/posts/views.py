from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post

AMOUNT = 10


def pag(request, post_list):
    paginator = Paginator(post_list, AMOUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


def index(request):
    """Главная страница."""
    title = 'Последние обновления на сайте'
    post_list = Post.objects.select_related('group', 'author')
    page_obj = pag(request, post_list)
    context = {
        'title': title,
        'page_obj': page_obj
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    """Страница со списком групп."""
    group = get_object_or_404(Group, slug=slug)
    post_list = group.groups_post.select_related('group', 'author')
    page_obj = pag(request, post_list)
    title = f'Записи сообщества {group}'
    context = {
        'group': group,
        'title': title,
        'page_obj': page_obj
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    user = get_object_or_404(User, username=username)
    post_list = user.posts.select_related('group', 'author')
    page_obj = pag(request, post_list)
    if request.user.is_authenticated:
        following = Follow.objects.filter(user=request.user, author=user)
        context = {
            'author': user,
            'page_obj': page_obj,
            'posts_count': user.posts.count(),
            'following': following,
        }
    else:
        context = {
            'author': user,
            'page_obj': page_obj,
            'posts_count': user.posts.count(),
        }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    posts = get_object_or_404(
        Post.objects.select_related('author', 'group'), id=post_id)
    posts_count = posts.author.posts.count()
    comments = Comment.objects.filter(post=posts)
    form = CommentForm()
    context = {
        'posts': posts,
        'posts_count': posts_count,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=request.user.username)
    form = PostForm()
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'post': post,
        'is_edit': True,
        'form': form,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    page_obj = pag(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    is_follower = Follow.objects.filter(user=user, author=author)
    if user != author and not is_follower.exists():
        Follow.objects.create(user=user, author=author)
    return redirect('posts:profile', username=request.user.username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follower = Follow.objects.filter(user=request.user, author=author)
    if follower.exists():
        follower.delete()
    return redirect('posts:profile', username=author)

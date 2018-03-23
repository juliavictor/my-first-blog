from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from .models import Post, Comment
from .forms import PostForm, CommentForm
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
import pandas as pd
from random import shuffle
import numpy as np
import sys

def post_list(request):
    recs = pd.read_csv('/home/juliavictor/my-first-blog/recommend.csv')
    if not request.session.session_key:
        request.session.save()

    #sum_values = recs.sum(axis=0).astype(str).sort_values(ascending=False)
    #filter = sum_values.str.contains("[a-z]")
    #sum_values = sum_values[~filter]

    # print(sum_values, file=sys.stderr)

    # excluding watched posts
    #session_data = recs.loc[recs['session_id'] == request.session.session_key]
    #if not session_data.empty:
    #    posts = Post.objects
    #    for post in session_data.columns[(session_data == 1).iloc[0]]:
    #        if post != 'session_id':
    #           posts = posts.exclude(id=post)
    #else:
    #    posts = Post.objects
    #posts = Post.objects

    posts = form_recommendations(request)
    # print(posts, file=sys.stderr)

    # 1 most popular post
    pop_post = Post.objects
    for post in posts:
        pop_post = pop_post.exclude(id=str(post.pk))

    posts = [x for x in posts] + \
            [y for y in pop_post.filter(published_date__lte=timezone.now()).order_by('-views')[:1]]

    # 1 newest post
    new_post = Post.objects
    for post in posts:
        new_post = new_post.exclude(id=str(post.pk))

    posts = [x for x in posts] + \
            [z for z in new_post.filter(published_date__lte=timezone.now()).order_by('-published_date')[:1]]

    # sorting by desc and only 8 first popular posts

    # posts = [x for x in posts.filter(published_date__lte=timezone.now()).order_by('-views')[:6]] + \
    #        [y for y in posts.filter(published_date__lte=timezone.now()).order_by('-published_date')[:2]]

    # posts = Post.objects.filter(published_date__lte=timezone.now()).order_by('-published_date')[:8]

    return render(request, 'blog/post_list.html', {'posts': posts})


def form_recommendations(request):
    # form list of 6 categories
    recs = pd.read_csv('/home/juliavictor/my-first-blog/categories.csv')

    # print("post_detail key", file=sys.stderr)

    # By default
    # posts = Post.objects.filter(published_date__lte=timezone.now()).order_by('-views')[:6]

    if not request.session.session_key:
        request.session.save()

    # if user is new, fill all categories with 10
    if not any(recs.session_id == request.session.session_key):
        data = pd.DataFrame({'session_id': [request.session.session_key]})
        for i in range(1,11):
            data.ix[data.session_id == request.session.session_key, str(i)] = 10
        recs = recs.append(data)

        # show 6 most popular posts
        posts = Post.objects.filter(published_date__lte=timezone.now()).order_by('-views')[:6]

    else:
        #[recs['session_id'] == request.session.session_key]
        session_data = recs.loc[recs['session_id'] == request.session.session_key]
        session_data = session_data.drop(['session_id'], axis=1)

        # sorting categories list by descending order
        session_data = session_data.iloc[:, np.argsort(session_data.iloc[0])]

        # selecting top 6 categories for this user
        cat_list = session_data.columns.values[-6:]
        shuffle(cat_list)

        # selecting 1 random post from each category
        posts = []
        for category in cat_list:
            posts = [x for x in posts] + [y for y in Post.objects.filter(tag=category).order_by('?')[:1]]

    # decrease tag values of shown posts by 0.1
    for post in posts:
        recs.ix[recs.session_id == request.session.session_key, str(post.tag)] -= 0.1

    recs.to_csv('/home/juliavictor/my-first-blog/categories.csv', encoding='utf-8', index=False)

    return posts




def post_detail(request, pk):
    # After post view we change the table for collaborative filtering
    recs = pd.read_csv('/home/juliavictor/my-first-blog/recommend.csv')
    cats = pd.read_csv('/home/juliavictor/my-first-blog/categories.csv')

    # print("post_detail key", file=sys.stderr)
    # Fix for none session_key

    if not request.session.session_key:
        request.session.save()

    if not any(recs.session_id == request.session.session_key):
        data = pd.DataFrame({'session_id': [request.session.session_key]})
        recs = recs.append(data)

    recs.ix[recs.session_id == request.session.session_key, str(pk)] = 1
    post = get_object_or_404(Post, pk=pk)

    # Unique views counter setting
    post.views = recs[pk].sum()
    post.save()

    cats.ix[cats.session_id == request.session.session_key, str(post.tag)] += 0.8

    recs.to_csv('/home/juliavictor/my-first-blog/recommend.csv', encoding='utf-8', index=False)
    cats.to_csv('/home/juliavictor/my-first-blog/categories.csv', encoding='utf-8', index=False)

    # For black & white filter
    request.session[pk] = 1
    return render(request, 'blog/post_detail.html', {'post': post})



@login_required
def post_new(request):
    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('post_detail', pk=post.pk)
    else:
        form = PostForm()
    return render(request, 'blog/post_edit.html', {'form': form})

@login_required
def post_edit(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == "POST":
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('post_detail', pk=post.pk)
    else:
        form = PostForm(instance=post)
    return render(request, 'blog/post_edit.html', {'form': form})

@login_required
def post_draft_list(request):
    posts = Post.objects.filter(published_date__isnull=True).order_by('created_date')
    return render(request, 'blog/post_draft_list.html', {'posts': posts})

@login_required
def post_publish(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.publish()
    return redirect('post_detail', pk=pk)

@login_required
def post_remove(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.delete()
    return redirect('post_list')

def add_comment_to_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.save()
            return redirect('post_detail', pk=post.pk)
    else:
        form = CommentForm()
    return render(request, 'blog/add_comment_to_post.html', {'form': form})

@login_required
def comment_approve(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    comment.approve()
    return redirect('post_detail', pk=comment.post.pk)

@login_required
def comment_remove(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    comment.delete()
    return redirect('post_detail', pk=comment.post.pk)
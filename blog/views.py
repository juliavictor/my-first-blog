from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from .models import Post, Comment
from .forms import PostForm, CommentForm
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from random import shuffle
import pandas as pd
import numpy as np
import sys
import random
from pathlib import Path
from django.template import RequestContext

# Bug-fix function, twice excluding in order to produce sliceable set
def random_value(posts):
    un_posts = Post.objects
    top_posts = Post.objects

    for post in posts:
        un_posts = un_posts.exclude(id=str(post.pk))

    for post in un_posts:
        top_posts = top_posts.exclude(id=str(post.pk))

    return top_posts.filter(published_date__lte=timezone.now()).order_by('?')[:1]


def read_file(name):
    filepath = Path(name)
    if filepath.exists():
        file = pd.read_csv(name)
    else:
        file = pd.read_csv('/home/juliavictor/my-first-blog/'+name)
    return file


def write_file(df, name):
    filepath = Path(name)
    if filepath.exists():
        file = df.to_csv(name, encoding='utf-8', index=False)
    else:
        file = df.to_csv('/home/juliavictor/my-first-blog/'+name,
                    encoding='utf-8', index=False)


def post_list(request):
    # recs = pd.read_csv('/home/juliavictor/my-first-blog/recommend.csv')
    recs = read_file('recommend.csv')
    if not request.session.session_key:
        request.session.save()

    posts = form_recommendations(request)

    # 1 most popular post
    pop_post = Post.objects
    for post in posts:
        pop_post = pop_post.exclude(id=str(post.pk))
    pop_post = pop_post.filter(published_date__lte=timezone.now()).order_by('-views')[:7]

    posts = [x for x in posts] + \
            [y for y in random_value(pop_post)]

    # 1 newest post
    new_post = Post.objects
    for post in posts:
        new_post = new_post.exclude(id=str(post.pk))
    new_post = new_post.filter(published_date__lte=timezone.now()).order_by('-published_date')[:7]

    posts = [x for x in posts] + \
            [z for z in random_value(new_post)]

    return render(request, 'blog/post_list.html', {'posts': posts})


def form_recommendations(request):
    # form list of 6 categories
    recs = read_file('categories.csv')

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

    write_file(recs, 'categories.csv')

    return posts




def post_detail(request, pk):
    # After post view we change the table for collaborative filtering
    recs = read_file('recommend.csv')
    cats = read_file('categories.csv')

    # Fix for none session_key
    if not request.session.session_key:
        request.session.save()

    if not any(recs.session_id == request.session.session_key):
        data = pd.DataFrame({'session_id': [request.session.session_key]})
        recs = recs.append(data)

    # if no one ever viewed this post
    if str(pk) not in recs.columns.values:
        # print(pk)
        # print(recs.columns.values)
        # print("i am here")
        recs.ix[recs.session_id == request.session.session_key, str(pk)] = 0

    # if this user never watched this post
    if recs.loc[recs.session_id == request.session.session_key, str(pk)].item() not in (1,0,-1):
        # print("i guess here we have NONE")
        recs.ix[recs.session_id == request.session.session_key, str(pk)] = 0

    poll_value = recs.loc[recs.session_id == request.session.session_key, str(pk)].item()

    for_val = 0
    against_val = 0

    if poll_value != 0:
        # print("This user already voted")
        # print(recs[pk].value_counts())
        values = recs[pk].value_counts().index.tolist()
        counts = recs[pk].value_counts().tolist()
        for value, count in zip(values, counts):
            if value == 1.0:
                for_val = count
            if value == -1.0:
                against_val = count
            # print(value, count)

    # fixing percentages
    sum = for_val + against_val
    if sum != 0:
        for_val = int(round(for_val*100/sum))
        against_val = int(round(against_val*100/sum))

    post = get_object_or_404(Post, pk=pk)

    # Unique views counter setting
    post.views = recs[pk].count()
    post.save()

    cats.ix[cats.session_id == request.session.session_key, str(post.tag)] += 0.8

    write_file(recs, 'recommend.csv')
    write_file(cats, 'categories.csv')

    # For black & white filter
    request.session[pk] = 1

    posts = Post.objects
    posts = posts.exclude(id=str(post.pk))
    posts = posts.filter(tag=post.tag).order_by('?')[:3]


    return render(request, 'blog/post_detail.html',
                  {'post': post, 'posts': posts, 'poll_value': poll_value,
                   'for_val': for_val, 'against_val': against_val})


def submit_poll(request, pk):
    # Fix for none session_key
    if not request.session.session_key:
        request.session.save()

    answer = request.POST.get('group-poll')
    # print("I am in submit_poll. Answer value is")
    # print(answer)
    if (answer == "1"):
        answer = 1
    else:
        answer = -1
    # Refreshing table values
    recs = read_file('recommend.csv')
    recs.ix[recs.session_id == request.session.session_key, str(pk)] = answer
    write_file(recs, 'recommend.csv')


    # Reloading the page
    return post_detail(request, pk)


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

@login_required
def home(request):
    return render(request, 'core/home.html')
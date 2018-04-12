from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from .models import Post, Comment, Poll
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

    # # For debug
    # if request.user.is_authenticated():
    #     print(request.user)
    #     print(request.user.id)
    #     print(request.user.first_name)
    #     print(request.user.last_name)
    # else:
    #     print(request.session.session_key)


    return render(request, 'blog/post_list.html', {'posts': posts})


def get_user_key(request):
    if request.user.is_authenticated():
        user_key = request.user.id
    else:
        user_key = request.session.session_key
    return str(user_key)


def form_recommendations(request):
    # form list of 6 categories
    recs = read_file('categories.csv')

    if not request.session.session_key:
        request.session.save()

    user_key = get_user_key(request)

    # if user is new, fill all categories with 10
    if not any(recs.session_id == user_key):
        data = pd.DataFrame({'session_id': [user_key]})
        for i in range(1,11):
            data.loc[data.session_id == user_key, str(i)] = 10
        recs = recs.append(data)

        # show 6 most popular posts
        posts = Post.objects.filter(published_date__lte=timezone.now()).order_by('-views')[:6]

    else:
        session_data = recs.loc[recs['session_id'] == user_key]
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
        recs.loc[recs.session_id == user_key, str(post.tag)] -= 0.1

    write_file(recs, 'categories.csv')

    return posts


def post_detail(request, pk):
    # After post view we change the table for collaborative filtering
    recs = read_file('recommend.csv')
    cats = read_file('categories.csv')
    polls = read_file('polls.csv')

    post = get_object_or_404(Post, pk=pk)

    # Fix for none session_key
    if not request.session.session_key:
        request.session.save()

    user_key = get_user_key(request)

    if not any(polls.session_id == user_key):
        data = pd.DataFrame({'session_id': [user_key]})
        recs = recs.append(data)
        polls = polls.append(data)

    # if no one ever viewed this post
    if str(pk) not in recs.columns.values:
        recs.loc[recs.session_id == user_key, str(pk)] = 0

    # if this user never watched this post
    if recs.loc[recs.session_id == user_key, str(pk)].item() not in (0,1,2,3,4,5):
        recs.loc[recs.session_id == user_key, str(pk)] = 0

    # Plotting results
    # In loop getting results of all polls

    js_results = []
    poll_value = 0
    # !! const_value for graph visualisation
    const = 1

    for poll in post.polls.all():
        poll_value = polls.loc[polls.session_id == user_key,
                               str(poll.id)].item()
        array = [0, 0, 0, 0, 0]

        if poll_value > 0:
            # print("This user already voted")
            values = polls[str(poll.id)].value_counts().index.tolist()
            counts = polls[str(poll.id)].value_counts().tolist()
            for value, count in zip(values, counts):
                for element in range(0, 5):
                    if value == element+1:
                        array[element] = count

            # Adding constant to every value
            array = [x + const for x in array]

            # Counting percentages
            sum_array = sum(array)
            if sum_array != 0:
                for element in range(0, 5):
                    array[element] = int(round(array[element]*100/sum_array))

            # Completing the final array
            array = list(reversed(array))
            array.append(poll.id)
            array.append(poll.question)
            js_results.append(array)

        else:
            poll_value = 0
            # print("This user never voted")
            break

    # Unique views counter setting
    post.views = recs[pk].count()
    post.save()

    cats.loc[cats.session_id == user_key, str(post.tag)] += 0.8

    write_file(recs, 'recommend.csv')
    write_file(cats, 'categories.csv')
    write_file(polls, 'polls.csv')

    # For black & white filter
    request.session[pk] = 1

    posts = Post.objects
    posts = posts.exclude(id=str(post.pk))
    posts = posts.filter(tag=post.tag).order_by('?')[:3]

    # polls = random.shuffle([i for i in post.polls.all()])

    return render(request, 'blog/post_detail.html',
                  {'post': post, 'posts': posts, 'js_results': js_results,
                   'poll_value': poll_value})


def submit_poll(request, pk):
    # Fix for none session_key
    if not request.session.session_key:
        request.session.save()

    user_key = get_user_key(request)
    post = get_object_or_404(Post, pk=pk)
    polls = read_file('polls.csv')

    for poll in post.polls.all():
        answer = request.POST.get('likert'+str(poll.id))
        # print("I am in submit_poll. Answer value is")
        # print(answer)
        polls.loc[polls.session_id == user_key, str(poll.id)] = answer

    write_file(polls, 'polls.csv')

    # Reloading the page
    return post_detail(request, pk)


def isNaN(num):
    return num != num


@login_required
def show_user_profile(request):
    # Fix for none session_key

    if not request.session.session_key:
        request.session.save()

    user_key = get_user_key(request)

    # Getting all polls this user voted
    posts = Post.objects.filter(published_date__lte=timezone.now()).order_by('-views')
    polls = read_file('polls.csv')
    poll_texts = []
    cmap = {1: 'Абсолютно не согласен', 2: 'Скорее не согласен',
            3: 'Отношусь нейтрально', 4: 'Скорее согласен',
            5: 'Совершенно согласен'}

    for post in posts:
        for poll in post.polls.all():
            if not polls.loc[polls.session_id == user_key].empty:
                value = polls.loc[polls.session_id == user_key,
                              str(poll.id)].item()
                if not isNaN(value):
                    value = cmap[value]
                    poll_texts.append((poll, value))


    return render(request, 'blog/user_profile.html', {'poll_texts': poll_texts})


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
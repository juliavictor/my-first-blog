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
import sqlite3
import datetime
import vk_api
from .auth_info import vk_username, vk_password
import os
from django.template import RequestContext
import avinit

def connect_to_database():
    # print(os.getcwd())
    if os.getcwd() == "C:\\Users\\Yulia\\proetcontra":
        con = sqlite3.connect('db.sqlite3', timeout=10)
    else:
        con = sqlite3.connect('proetcontra/db.sqlite3', timeout=10)
    return con


def get_user_profile_pic(request):
    if str(request.user)[:1]!="id":
        return ""

    cur_user_id = str(request.user)[2:]

    vk_session = vk_api.VkApi(vk_username, vk_password)
    vk_session.auth()

    vk = vk_session.get_api()

    user_info = vk.users.get(user_id=cur_user_id, fields='photo_100')[0]

    return user_info['photo_100']



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

    if not request.session.session_key:
        request.session.save()

    user_key = get_user_key(request)

    # Connecting to database
    con = connect_to_database()
    cursor = con.cursor()

    user_posts = pd.read_sql_query("select user_id, post_id from "
                                  "blog_post_recs where "
                                   "user_id=\"" + str(user_key) + "\"", con)

    posts = Post.objects.filter(published_date__lte=timezone.now()).order_by('-views')
    # If this user never appeared before
    if user_posts.empty:
        for post in posts:
            t = (user_key, post.pk, post.tag, 10)
            cursor.execute('insert into blog_post_recs(user_id,post_id,category,value)'
                           ' values (?,?,?,?)', t)
        con.commit()
    else:
        # updating new posts
        for post in posts:
            if post.pk not in user_posts["post_id"].tolist():
                t = (user_key, post.pk, post.tag, 10)
                cursor.execute('insert into blog_post_recs(user_id,post_id,category,value)'
                               ' values (?,?,?,?)', t)
        con.commit()


    user_cats = pd.read_sql_query("select user_id, category, value from "
                                  "blog_post_categories where "
                                   "user_id=\"" + str(user_key) + "\"", con)

    if user_cats.empty:
        # if user is new, fill all categories with 10
        for i in range(1, 11):
           t = (user_key, i, 10)
           cursor.execute('insert into blog_post_categories(user_id,category,value)'
                          ' values (?,?,?)', t)
        con.commit()

        # show 6 most popular posts
        posts = Post.objects.filter(published_date__lte=timezone.now()).order_by('-views')[:6]

    else:
        # sorting categories list by descending order
        user_cats = user_cats.sort_values('value', ascending=False)

        # selecting top 6 categories for this user
        cat_list = user_cats['category'][:6].tolist()
        shuffle(cat_list)

        posts = []
        # print("List of categories:")
        # print(cat_list)
        for category in cat_list:
            # selecting 1 best post from each category
            cursor.execute("select post_id, max(value) as date from blog_post_recs "
                           "where category=" + str(category) +
                           " and user_id=\"" + str(user_key) + "\"")
            post_id = cursor.fetchone()[0]

            # print("Best post from category: "+str(category))
            # print(post_id)

            posts = [x for x in posts] + [y for y in Post.objects.filter(pk=post_id).order_by('?')[:1]]


    for post in posts:
        # decrease tag values of shown posts by 0.1
        cursor.execute("update blog_post_categories set value = value - 0.1"
                       " where category = " + str(post.tag) +
                       " and user_id=\"" + str(user_key) + "\"")

        # decrease values of shown posts by 0.1
        cursor.execute("update blog_post_recs set value = value - 0.1"
                       " where post_id = " + str(post.pk) +
                       " and user_id=\"" + str(user_key) + "\"")

    con.commit()
    cursor.close()
    con.close()

    return posts


def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)

    # Fix for none session_key
    if not request.session.session_key:
        request.session.save()

    user_key = get_user_key(request)

    # Connecting to database
    con = connect_to_database()
    cursor = con.cursor()

    # Adding view to log
    t = (user_key, pk, datetime.datetime.now())
    cursor.execute('insert into blog_post_views(user_id,post_id,date) values (?,?,?)', t)
    con.commit()

    # if not any(polls.session_id == user_key):
    #     data = pd.DataFrame({'session_id': [user_key]})
    #     recs = recs.append(data)
    #     polls = polls.append(data)

    # # if no one ever viewed this post
    # if str(pk) not in recs.columns.values:
    #     recs.loc[recs.session_id == user_key, str(pk)] = 0
    #
    # # if this user never watched this post
    # if recs.loc[recs.session_id == user_key, str(pk)].item() not in (0,1,2,3,4,5):
    #     recs.loc[recs.session_id == user_key, str(pk)] = 0

    # Plotting results
    # In loop getting results of all polls

    js_results = []
    poll_value = 0
    # !! const_value for graph visualisation
    const = 1

    for poll in post.polls.all():
        array = [0, 0, 0, 0, 0]
        post_value = pd.read_sql_query("SELECT * FROM blog_poll_values where post_id=" + pk +
                                       " and user_id=\"" + str(user_key) + "\"", con)

        if not post_value.empty:
            poll_value = 1
            # print("This user already voted")

            post_values = pd.read_sql_query("select value, count(value) from (select user_id, "
                  "blog_poll_id, value, max(date) as date from blog_poll_values where "
                  "blog_poll_id="+str(poll.id)+" group by user_id) group by value", con)

            values = post_values['value'].tolist()
            counts = post_values['count(value)'].tolist()

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
    cursor.execute("select user_id, post_id, max(date) as date from blog_post_views "
                   "where post_id=" + pk + " group by user_id")
    post.views = len(cursor.fetchall())

    # Increasing value by 0.8
    cursor.execute("update blog_post_categories set value = value + 0.8"
                       " where category = " + str(post.tag) +
                       " and user_id=\"" + str(user_key) + "\"")

    # Decrease values of shown post by 1
    cursor.execute("update blog_post_recs set value = value - 1"
                   " where post_id = " + str(post.pk) +
                   " and user_id=\"" + str(user_key) + "\"")

    con.commit()
    cursor.close()
    con.close()

    post.save()

    # For black & white filter
    request.session[pk] = 1

    posts = Post.objects
    posts = posts.exclude(id=str(post.pk))
    posts = posts.filter(tag=post.tag).order_by('?')[:3]

    # polls = random.shuffle([i for i in post.polls.all()])

    # Comments section
    if request.method == "POST":
        if 'post-comment' in request.POST:
            form = CommentForm(request.POST)
            if form.is_valid():
                comment = form.save(commit=False)
                comment.author = request.user
                comment.post = post
                comment.save()
                return redirect('post_detail', pk=post.pk)
        else:
            form = CommentForm()
    else:
        form = CommentForm()

    if request.user.is_authenticated:
        svg_tag = svg_avatar(form_username(request.user))
    else:
        svg_tag = ""

    post_comments = []

    for comment in post.comments.all():
        line = {}
        line["author"] = form_username(comment.author)
        line["created_date"] = comment.created_date
        line["text"] = comment.text
        svg = svg_avatar(line["author"])
        line["svg"] = svg
        post_comments.append(line)

    return render(request, 'blog/post_detail.html',
                  {'post': post, 'posts': posts, 'js_results': js_results,
                   'poll_value': poll_value, 'form': form, 'svg_tag': svg_tag,
                   'post_comments': post_comments})


def svg_avatar(username):
    svg_tag = avinit.get_svg_avatar(username)
    svg_tag = svg_tag.replace("200px", "50px")\
        .replace("80px","24px").replace("200","50")
    return svg_tag


def form_username(user):
    # User name
    fn = user.first_name
    ln = user.last_name
    if len(ln) > 0:
        user_name = fn + ' ' + ln
    else:
        if len(fn) > 0:
            user_name = fn
        else:
            user_name = str(user)
    return user_name



def submit_poll(request, pk):
    # Fix for none session_key
    if not request.session.session_key:
        request.session.save()

    user_key = get_user_key(request)
    post = get_object_or_404(Post, pk=pk)

    # Connecting to database
    con = connect_to_database()
    cursor = con.cursor()

    for poll in post.polls.all():
        answer = request.POST.get('likert'+str(poll.id))

        # Adding new values
        t = (user_key, pk, poll.id, answer, datetime.datetime.now())
        cursor.execute('insert into blog_poll_values(user_id,post_id,blog_poll_id,value,date) values (?,?,?,?,?)', t)
        con.commit()

    cursor.close()
    con.close()

    # Reloading the page
    return post_detail(request, pk)


def isNaN(num):
    return num != num


@login_required
def show_vk_info(request):
    if not request.session.session_key:
        request.session.save()

    vk_session = vk_api.VkApi(vk_username, vk_password)
    vk_session.auth()

    vk = vk_session.get_api()
    cur_user_id = str(request.user)[2:]

    user_info = vk.users.get(user_id=cur_user_id, fields='interests')[0]

    # print(user_info)

    username = user_info['first_name'] + " " + user_info['last_name']

    group_list = vk.groups.get(user_id=cur_user_id, extended=1, fields="description")

    newsfeed = vk.wall.get(owner_id=cur_user_id, count=100)

    # print(newsfeed)

    # if group_list['count'] != 0:
    #     for group in group_list['items']:
    #         print(group['name'])
    #         print(group['description'])


    return render(request, 'blog/vk_info.html', {'username': username, 'groups': group_list, 'feed': newsfeed})



@login_required
def show_user_profile(request):
    # Fix for none session_key

    if not request.session.session_key:
        request.session.save()

    user_key = get_user_key(request)

    # Connecting to database
    con = connect_to_database()
    cursor = con.cursor()

    # Getting all polls this user voted
    posts = Post.objects.filter(published_date__lte=timezone.now()).order_by('-views')
    poll_texts = []
    cmap = {1: 'Абсолютно не согласен', 2: 'Скорее не согласен',
            3: 'Отношусь нейтрально', 4: 'Скорее согласен',
            5: 'Совершенно согласен'}

    for post in posts:
        for poll in post.polls.all():
            post_val = pd.read_sql_query("select user_id, blog_poll_id, post_id, value, "
                  "max(date) as date from blog_poll_values where blog_poll_id="
                  + str(poll.id) + " and user_id=\"" + str(user_key) + "\"", con)

            if post_val['value'][0] is not None:
                value = post_val['value'][0]
                date = post_val['date'][0].split()
                date = date[0].split("-")
                # print(date)

                if not isNaN(value):
                    value = cmap[value]
                    poll_texts.append((poll, value, date))

    cursor.close()
    con.close()


    # Loading VK user image
    profile_pic = get_user_profile_pic(request)

    # User name
    fn = request.user.first_name
    ln = request.user.last_name
    if len(ln) > 0:
        user_name = fn + ' ' + ln
    else:
        if len(fn) > 0:
            user_name = fn
        else:
            user_name = request.user

    return render(request, 'blog/user_profile.html', {'poll_texts': poll_texts,
                                                      'profile_pic': profile_pic,
                                                      'user_name': user_name})


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
            fn = request.user.first_name
            ln = request.user.last_name
            if len(ln) > 0:
                comment.author = fn + ' ' + ln
            else:
                if len(fn) > 0:
                    comment.author = fn
                else:
                    comment.author = request.user
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
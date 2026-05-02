from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import PostForm
from .models import Post
from django.shortcuts import  get_object_or_404


@login_required
def create_post(request):

    if request.method == 'POST':
        form = PostForm(request.POST)

        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user  # assign current logged-in user
            post.save()
            return redirect('feed')  # redirect to feed page

    else:
        form = PostForm()

    return render(request, 'feed/create_post.html', {'form': form})

# Create your views here.



def feed_view(request):
    posts = Post.objects.all().order_by('-created_at')
    return render(request, 'feed/feed.html', {'posts': posts})



def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    return render(request, 'feed/post_detail.html', {'post': post})
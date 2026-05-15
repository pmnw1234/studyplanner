from django.shortcuts import render

from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import Review
from .forms import ReviewForm

@login_required
def add_review(request, username):

    reviewed_user = get_object_or_404(
        User,
        username=username
    )

    if reviewed_user == request.user:
        return redirect(
            'view_other_profile',
            user_id=reviewed_user.id
        )

    if request.method == 'POST':

        form = ReviewForm(request.POST)

        if form.is_valid():

            review = form.save(commit=False)

            review.reviewer = request.user
            review.reviewed_user = reviewed_user

            review.save()
        else:
            print("FORM ERRORS:", form.errors)

    return redirect(
        'view_other_profile',
        user_id=reviewed_user.id
    )

# Create your views here.

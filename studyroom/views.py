from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import StudyRoom, RoomActivity
from .forms import StudyRoomForm


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import StudyRoom, RoomActivity
from .forms import StudyRoomForm


@login_required
def studyroom_dashboard(request):
    my_rooms = request.user.study_rooms.all() | request.user.created_rooms.all()

    form = StudyRoomForm()

    return render(request, 'studyroom/dashboard.html', {
        'my_rooms': my_rooms.distinct(),
        'form': form
    })


@login_required
def create_room(request):
    if request.method == 'POST':
        form = StudyRoomForm(request.POST)

        if form.is_valid():
            room = form.save(commit=False)
            room.creator = request.user
            room.save()

            room.members.add(request.user)

            RoomActivity.objects.create(
                room=room,
                user=request.user,
                action='Created room'
            )

            messages.success(request, "Study room created successfully!")

    return redirect('studyroom_dashboard')


@login_required
def join_room(request):
    if request.method == 'POST':
        code = request.POST.get('room_code', '').strip().upper()

        try:
            room = StudyRoom.objects.get(room_code=code)

            if request.user in room.members.all():
                messages.warning(request, "You already joined this room.")
                return redirect('studyroom_dashboard')

            if room.is_full():
                messages.error(request, "Room is full (max 3 members).")
                return redirect('studyroom_dashboard')

            room.members.add(request.user)

            RoomActivity.objects.create(
                room=room,
                user=request.user,
                action='Joined room'
            )

            messages.success(request, "Joined room successfully!")

        except StudyRoom.DoesNotExist:
            messages.error(request, "Invalid room code.")

    return redirect('studyroom_dashboard')


@login_required
def room_detail(request, room_id):
    room = get_object_or_404(StudyRoom, id=room_id)

    return render(request, 'studyroom/room_detail.html', {
        'room': room
    })

# Create your views here.

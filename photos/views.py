from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth import authenticate, login as _login, logout as _logout, get_user_model
from django.contrib.auth.decorators import login_required

from photoshare.utils.image_header import compress_img_by_bytesio
from .models import Category, Photo
from .forms import CustomUserCreationForm
# Create your views here.
from copy import deepcopy

User = get_user_model()


def login(request):
    """登陆视图"""
    page = 'login'

    if request.method == 'POST':
        _next = request.GET.get('next', reverse('photo:gallery'))
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)

        if user is not None:
            _login(request, user)
            return redirect(_next)

    return render(request, 'photos/login_register.html', {'page': page})


def logout(request):
    _logout(request)
    return redirect(reverse('photo:login'))


def register(request):
    form = CustomUserCreationForm()

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.save()

            _login(request, user)
            return redirect(reverse('photo:gallery'))

    context = {'form': form, 'page': 'register'}
    return render(request, 'photos/login_register.html', context)


def gallery(request):
    """index"""
    user = request.user
    category = request.GET.get('category')

    if isinstance(user, AnonymousUser):
        user = User.objects.get(username=settings.PUBLIC_USER_USERNAME)

    photos = Photo.objects.filter(category__user=user)

    if not request.user.is_authenticated:  # 未登陆只显示公开部分图片
        photos = photos.filter(public=True)

    if category is not None:
        photos = photos.filter(category__name=category)

    categories = Category.objects.filter(user=user)

    context = {'categories': categories, 'photos': photos, 'user': user}
    return render(request, 'photos/gallery.html', context)


@login_required
def add_photo(request):
    """添加图片"""
    if not request.method == 'POST':
        categories = request.user.category_set.all()

        context = {'categories': categories}
        return render(request, 'photos/add.html', context)

    category_name = request.POST.get('category') or request.POST.get('category_new')
    images = request.FILES.getlist('images')
    public = False if request.POST.get('public', '').lower() == 'false' else True
    description = request.POST.get('description', '')

    if not category_name:
        return redirect(reverse('photo:add'))
    if not images:
        return redirect(reverse('photo:add'))

    category, created = Category.objects.get_or_create(name=category_name, user=request.user)

    for imageHD in images:
        field_name = getattr(imageHD, 'field_name', None)

        image_bytesio = compress_img_by_bytesio(imgdata=deepcopy(imageHD.file), image_format=imageHD.file_format, datasize=imageHD.size)
        image = InMemoryUploadedFile(file=image_bytesio,
                                     name=imageHD.name.replace('.' + imageHD.name.split('.')[-1],
                                                               settings.THUMBANIL_SUFFIX + '.' + imageHD.file_format),
                                     content_type=imageHD.content_type, size=None, charset=imageHD.charset,
                                     content_type_extra=imageHD.content_type_extra, field_name=field_name)

        Photo.objects.create(
            category=category,
            description=description,
            image=image,  # 缩略图
            imageHD=imageHD,  # 高清图
            public=public,
        )

    return redirect(reverse('photo:gallery'))


def view_photo(request, pk):
    """查看照片"""
    user = request.user
    photo = Photo.objects.filter(id=pk)

    if user.is_authenticated:
        photo = photo.filter(category__user=user)
    else:
        photo = photo.filter(category__user__username=settings.PUBLIC_USER_USERNAME)

    photo = photo.first()

    return render(request, 'photos/photo.html', {'photo': photo})


def delete_photo(request, pk):
    """delete photo"""
    if not request.user.is_authenticated:
        url = reverse('photo:login') + f'?next={reverse("photo", args=[pk])}'
        return redirect(url)

    Photo.objects.filter(category__user=request.user, id=pk).delete()
    return redirect(reverse('photo:gallery'))


@login_required
def update_photo(request, pk):
    """更新照片信息"""
    # if request.method != 'GET':
    #     return redirect(reverse('photo:view'))
    public = request.GET.get('public')

    photo = Photo.objects.filter(id=pk, category__user=request.user).first()
    # photo = Photo.objects.filter(id=pk, category__user=User.objects.get(username=settings.PUBLIC_USER_USERNAME)).first()

    if photo is None:
        return redirect(reverse('photo:view'))

    if public is not None:
        if public.lower() == 'false':
            photo.public = False
        elif public.lower:
            photo.public = True

    photo.save()
    u = reverse('photo:view', args=[pk])
    return redirect(u)


def del_category(request):
    """delete category"""
    pass

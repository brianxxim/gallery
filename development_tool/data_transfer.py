from io import BytesIO

import requests
from django.conf import settings

from photos.models import Photo
from photoshare.utils.image_header import compress_img_by_bytesio
from photoshare.utils.qiniu_storage import upload_file, upload_data


def local_to_qiniu(start_pk=None, end_pk=None):
    """本地图片移动到七牛"""
    photos = Photo.objects.all()

    if isinstance(start_pk, int):
        photos = photos.filter(id__gte=start_pk)

    if isinstance(end_pk, int):
        photos = photos.filter(id__lte=end_pk)

    for photo in photos:
        name = photo.image.name
        # 上传到七牛并修改photo的name属性
        update_path = '{}/static/images/{}'.format(settings.BASE_DIR, name)
        new_name = upload_file(update_path)
        photo.image.name = new_name
        photo.save()
        print(f'上传完成: {name} to {new_name}')


def imageHD_to_image():
    """为旧图片提供压缩服务"""
    # 旧版本中高清图片存储在image字段, 新版本中高清图片在imageHD, 缩略图在image
    # 1.获取所有没有image字段的图片的Photo
    photos = Photo.objects.all()[2:]

    for photo in photos:
        filename = photo.image.name

        # 2.获取高清图片, 生成压缩图片
        #   2.1.获取图片中的图片url
        url = photo.image.url
        #   2.2.请求获取二进制图片数据
        content = requests.get(url).content
        #   2.3.压缩图片, 上传到七牛
        image_bytesio = compress_img_by_bytesio(BytesIO(content))
        new_filename = upload_data(image_bytesio.getvalue())

        # 3.修改photo并保存
        photo.imageHD.name = filename
        photo.image.name = new_filename

        photo.save()
        print(f'{photo.id}-{photo.description}完成 新文件名: {new_filename}')
    print('全部完成')


def imageHD_to_image2(name=None):
    """再次压缩imageHD"""
    photos = Photo.objects.all()

    if name:
        photos = photos.filter(imageHD=name)

    for photo in photos:
        filename = photo.imageHD.name
        url = photo.imageHD.url

        content = requests.get(url).content
        image_bytesio = compress_img_by_bytesio(BytesIO(content), 'jpeg', datasize=len(content))

        new_filename = upload_data(image_bytesio.getvalue(), key=filename + '=thumbnail')
        photo.image.name = new_filename

        photo.save()
        print(f'{photo.id}-{photo.description}完成 新文件名: {new_filename}')
    print('全部完成')


if __name__ == '__main__':
    imageHD_to_image()

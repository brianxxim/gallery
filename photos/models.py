from django.contrib.auth.models import User
from django.db import models


class Category(models.Model):
    """图片分类模型"""
    class Meta:
        verbose_name = '分类'
        verbose_name_plural = verbose_name

    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=100, null=False, blank=False)

    def __str__(self):
        return self.name


class Photo(models.Model):
    """照片模型"""
    class Meta:
        verbose_name = '照片'
        verbose_name_plural = verbose_name
    
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='类别')
    public = models.BooleanField(default=True, verbose_name='是否公开')
    image = models.ImageField(null=False, blank=False, verbose_name='缩略图')
    imageHD = models.ImageField(null=True, blank=False, verbose_name='高清图')
    description = models.TextField(verbose_name='简介')

    def __str__(self):
        return self.description

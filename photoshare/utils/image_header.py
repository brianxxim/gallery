import os
import pathlib
from io import BytesIO
from math import ceil
from PIL import Image
from django.conf import settings
from pyheif import read as read_heif


# 初始化压缩比例设置
COMPRESS_PROPORTION = [(size, ratio) for size, ratio in settings.COMPRESS_IMG_PROPORTION.items()]
COMPRESS_PROPORTION.reverse()


def compress_img_by_bytesio(imgdata, image_format: str = 'PNG', pdi_ratio: int = None, datasize: int = None):
    """
    压缩BytesIO类二进制图片
    :param image_format: 保存的图片格式 参考: https://www.osgeo.cn/pillow/handbook/image-file-formats.html
    :param imgdata: 二进制图片数据
    :param pdi_ratio: 分辨率压缩倍数
    :param datasize: 数据大小(b), 通过此参数计算pdi_ration(当pdi_ration为None时)
    :return:
    """

    # 1.压缩图片
    img = _compress_img(imgdata, pdi_ratio=pdi_ratio, datasize=datasize)

    # 2.保存bytesio图片
    bytesio_img = BytesIO()
    img.save(bytesio_img, image_format)

    # 3.返回bytesio类型图片,
    img.close()
    bytesio_img.seek(0)

    return bytesio_img


def convert_heif(fp, to_format='jpeg'):
    """
    转换heic图片
    :param fp: 图片对象, 可以是路径或二进制数据
    :param to_format: 目标格式
    :return:
    """

    heif_file = read_heif(fp)
    image = Image.frombytes(
        heif_file.mode,
        heif_file.size,
        heif_file.data,
        "raw",
        heif_file.mode,
        heif_file.stride,
    )

    if isinstance(fp, (str, pathlib.Path)):
        filename = fp.replace('.' + fp.split('.')[-1], '.' + to_format)
        image.save(filename, to_format)
        return filename

    else:
        bi = BytesIO()
        image.save(bi, to_format)
        bi.seek(0)

        if isinstance(fp, bytes):
            r = bi.read()
            bi.close()
            return r

        return bi


def _compress_img(fp: BytesIO or bytes or pathlib.Path, pdi_ratio: int = None, datasize: int = None):
    """
    压缩图片并返回
    :param pdi_ratio: 分辨率压缩倍数
    :param fp: 图片路径或BytesIO对象
    :param datasize: 数据大小(b), 通过此参数计算pdi_ration(当pdi_ration为None时)
    :return:
    """

    if isinstance(fp, bytes):
        fp = BytesIO(fp)

    if pdi_ratio is None:
        pdi_ratio = _get_compress_ratio(datasize)

    # 1. 压缩图片
    img = Image.open(fp)
    w, h = img.size
    # new_img = img.resize((int(w * pdi_ratio), int(h * pdi_ratio))) 当h或w小于10时, 使int(h * pdi_ratio)= 0
    new_img = img.resize((ceil(w * pdi_ratio), ceil(h * pdi_ratio)))

    # 2.关闭原图片、返回新图片
    img.close()
    return new_img


def _get_compress_ratio(datasize: int):
    """
    获取图片压缩比例
    :return:
    """
    if datasize is not None:
        datasize_mb = datasize / 1000 / 1000
        for proportion in COMPRESS_PROPORTION:
            if datasize_mb > proportion[0]:
                return proportion[1]

    return settings.DEFAULT_COMPRESS_IMG_PROPORTION


def compress_img_by_file(filepath, save_path=None, pdi_ratio: int = None, new_file_suffix='_thumbnail'):
    """
    压缩图片并保存(已废弃)
    文件名变更: xxx.jpg -> xxx_thumbnail.jpg
    :param new_file_suffix: 给新文件的后缀
    :param filepath: 文件路径
    :param save_path: 新文件保存路径, 默认为filepath的父路径
    :param pdi_ratio: 分辨率压缩倍数
    :return:
    """
    # xxx/xxx.jpg -> xxx/xxx_thumbnail.jpg
    # 方法1
    # prefix, suffix = filepath.split('.')
    # save_path = prefix if save_path is None else save_path
    # new_filepath = save_path + '_thumbnail' + suffix

    # 方法2
    dir_path, filename = os.path.split(filepath)
    prefix, suffix = os.path.splitext(filename)
    save_path = dir_path if save_path is None else save_path
    new_filepath = os.path.join(save_path, prefix + new_file_suffix + suffix)

    # 1.压缩图片
    new_img = _compress_img(filepath)
    # 2.保存图片
    new_img.save(new_filepath, pdi_ratio)
    # 3.关闭图片
    new_img.close()

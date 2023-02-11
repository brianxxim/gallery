from io import BytesIO

from django.conf import settings
from django.core.cache import cache
from django.core.files.storage import Storage
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.files.uploadhandler import FileUploadHandler as FileUploadHandler, StopUpload
from django.core.handlers.wsgi import WSGIRequest

from photoshare.utils.image_header import convert_heif
from photoshare.utils.qiniu_storage import upload_data


def global_variable(request):
    """全局上下文"""
    content = cache.get('global:variable')

    if not content:
        content = {
            'link_about_me': settings.LINK_ABOUT_ME,
            'username':  settings.PUBLIC_USER_USERNAME,
        }
        cache.set('global:variable', content, 60 * 60 * 12)

    return content


class FileStorage(Storage):
    """
    自定义django文件存储类
    """

    def __init__(self, qiniu_base_url=None):
        self.base_url = qiniu_base_url or settings.QINIU_STORAGE_PREFIX

    def _open(self, name, mode='rb'):
        """
        :param name: 要打开的文件的名字
        :param mode: 打开文件方式
        :return: None
        """
        pass

    def _save(self, name, content: InMemoryUploadedFile):
        """
        :param name: django生成的文件名
        :param content: 保存的文件对象
        :return string 保存到数据库的文件名
        """
        return upload_data(content.read())
        # return upload_data(content.read(), content.name)

    def url(self, name):
        """
        读取文件路径
        :param name: 数据库中保存的文件路径后缀
        :return: 文件完整路径
        """
        return self.base_url + name

    def exists(self, name):
        """
        校验文件是否已存在
        :param name:
        :return:
        """
        return False

    def delete(self, name):
        """
        同步删除七牛文件
        :param name:
        :return:
        """
        # TODO 待开发
        pass


class ImageUploadHandler(FileUploadHandler):
    """自定义文件上传处理器"""

    # django调用的顺序: handle_raw_input -> new_file -> receive_data_chunk -> file_complete
    def handle_raw_input(self, input_data: WSGIRequest, META, content_length, boundary, encoding=None):
        """一般用于初始化参数或修改http请求中的信息"""
        self.activated = content_length <= settings.FILE_UPLOAD_MAX_SIZE

    def new_file(self, field_name, file_name, content_type, content_length, charset=None, content_type_extra=None):
        """
        一般用于控制生成的self.file(保存在磁盘or内存?)
        引发StopFutureHandlers()异常以控制不进入下一个文件系统类；
        """
        super().new_file(field_name, file_name, content_type, content_length, charset, content_type_extra)
        self.file = BytesIO()

    def receive_data_chunk(self, raw_data, start):
        if not self.activated:
            # 文件太大, 不执行上传
            raise StopUpload()

        self.file.write(raw_data)

    def file_complete(self, file_size):
        self.file.seek(0)
        # 图片转换
        file_format = self.content_type.split('/')[-1]
        if file_format.lower() == 'heic':
            file_format = settings.HEIC_CONVERT_FORMAT

            uf = InMemoryUploadedFile(
                file=convert_heif(self.file, file_format),
                field_name=self.field_name,
                name=self.file_name.replace('.' + self.file_name.split('.')[-1], '.' + file_format),
                content_type=self.content_type.replace('heic', file_format),
                size=None,
                charset=self.charset,
                content_type_extra=self.content_type_extra
            )
        else:
            uf = InMemoryUploadedFile(
                file=self.file,
                field_name=self.field_name,
                name=self.file_name,
                content_type=self.content_type,
                size=file_size,
                charset=self.charset,
                content_type_extra=self.content_type_extra
            )

        uf.file_format = file_format
        return uf

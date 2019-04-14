from django.core.files import storage
from django.conf import settings
from fdfs_client.client import Fdfs_client


class FastDFSStorage(storage):
    """ 自定义django 文件存储系统 """

    def __init__(self, client_conf=None, base_url=None):
        self.client_conf = client_conf or settings.FDFS_CLIENT_CONF
        self.base_url = base_url or settings.FDFS_URL

    def _open(self, name, mode='rb'):
        """ 打开文件时要用的,目前用不到,但是必须要实现,so PASS """
        pass

    def _sava(self, name, content):
        """
        保存文件时要用的
        :param name: 文件名字
        :param content: 文件内容
        :return: 文件在fdfs的唯一标识(fileid)
        """
        client = Fdfs_client(self.client_conf)
        ret = client.upload_appender_by_buffer(content.read())
        if ret.get('Status') != 'Upload successed.':
            raise Exception('fastfds upload failed')
            # 返回结果
        file_id = ret.get('Remote file_id')
        return file_id

    def exists(self, name):
        """ 判断文件是否存在时调用的,返回false告诉django每次都是新的文件 """
        return False

    def url(self, name):
        """ 返回文件全路径 """
        return self.base_url + name

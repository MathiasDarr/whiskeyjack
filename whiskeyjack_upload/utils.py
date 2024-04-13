from posixpath import join
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage


BINDMOUNT_DIR = '/usr/src/app/appdata'


def store_file_to_bind_mount(file: FileStorage) -> str:
    filename = secure_filename(file.filename)
    filepath = join(BINDMOUNT_DIR, filename)
    file.save(filepath)
    return filepath

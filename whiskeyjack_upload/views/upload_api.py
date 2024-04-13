from flask import Blueprint, request

from whiskeyjack_upload.worker.rq_manager import RqManager
from whiskeyjack_upload.upload_worker import upload
from whiskeyjack_upload.utils import store_file_to_bind_mount

api = Blueprint("upload_api", __name__)


@api.route("/")
def index():
    return "ephemeral"

@api.route('/upload', methods=['POST'])
def upload_route():
    files = request.files.getlist("files")
    if files and len(files) >= 1:
        filepath = store_file_to_bind_mount(files[0])
        RqManager.enqueue(
            upload, {
                'filepath': filepath,
            },
            queue='upload'
        )

    return "upload"

def mount_app_blueprints(app):
    app.register_blueprint(api)
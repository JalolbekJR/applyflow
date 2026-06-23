from django.conf import settings
from django.core.files.uploadhandler import FileUploadHandler, StopUpload


class BoundedDocumentUploadHandler(FileUploadHandler):
    """Abort the singleton CV file part once it exceeds the application limit."""

    def __init__(self, request=None):
        super().__init__(request)
        self._current_field_name = None
        self._current_size = 0
        self._file_count = 0

    def new_file(self, *args, **kwargs):
        super().new_file(*args, **kwargs)
        self._current_field_name = self.field_name
        self._current_size = 0
        self._file_count += 1
        if self.field_name != "file" or self._file_count > 1:
            self.request._applyflow_document_invalid_multipart = True
            raise StopUpload(connection_reset=False)

    def receive_data_chunk(self, raw_data, start):
        if self._current_field_name is not None:
            self._current_size += len(raw_data)
            if self._current_size > settings.DOCUMENT_MAX_UPLOAD_BYTES:
                self.request._applyflow_document_upload_too_large = True
                raise StopUpload(connection_reset=False)
        return raw_data

    def file_complete(self, file_size):
        return None

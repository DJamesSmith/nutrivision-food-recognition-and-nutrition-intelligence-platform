import logging
logger = logging.getLogger(__name__)


# Deletes a FieldFile from storage, tolerating the case where it's already gone.
# Never raises — a missing/undeletable file must not block the database operation that triggered the cleanup.
def delete_file_if_exists(field_file):
    if not field_file:
        return
    try:
        storage = field_file.storage
        name = field_file.name
        if name and storage.exists(name):
            storage.delete(name)
    except Exception:
        logger.exception("Failed to delete file '%s' from storage.", getattr(field_file, 'name', '?'))


# Fetches the currently-persisted 'image' field value for a row about to be updated,
# so it can be compared against the incoming value in a pre_save receiver. Returns None for new (unsaved) instances.
def get_previous_file(model_cls, pk):
    if not pk:
        return None
    try:
        return model_cls.objects.only('image').get(pk=pk).image
    except model_cls.DoesNotExist:
        return None

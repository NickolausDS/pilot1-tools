import json


class PilotClientException(Exception):
    pass


class RequiredUploadFields(PilotClientException):

    def __init__(self, message, fields, *args, **kwargs):
        self.message = message
        self.fields = fields

    def __str__(self):
        example = {f: '<VALUE>' for f in self.fields}
        return ('{}. Please provide minimum fields with the -j flag. Example:'
                '\n {}'.format(self.message, json.dumps(example, indent=4)))


class NoEntryToUpdate(PilotClientException):
    """An update was attempted, but no dataframe was provided and no search
    record currently exists"""
    pass


class DataframeException(PilotClientException):
    def __init__(self, *args, dataframe_info, **kwargs):
        super().__init__(*args, **kwargs)
        self.dataframe_info = dataframe_info


class ContentMismatch(DataframeException):
    """Updating a search entry was aborted due to a previous entry's
    content not matching. This error was raised to prevent accidentally
    overwriting it."""
    pass

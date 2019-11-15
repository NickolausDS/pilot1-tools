import os
import pytest
import json
from unittest.mock import Mock

import globus_sdk
import jsonschema
from pilot.search import scrape_metadata
from pilot import exc, analysis
from pilot.exc import AnalysisException
from tests.unit.mocks import COMMANDS_FILE_BASE_DIR, MULTI_FILE_DIR

EMPTY_TEST_FILE = os.path.join(COMMANDS_FILE_BASE_DIR,
                               'test_file_zero_length.txt')
EMTPY_TEST_FILE_META = os.path.join(COMMANDS_FILE_BASE_DIR,
                                    'empty_file_metadata.json')
SMALL_TEST_FILE = os.path.join(COMMANDS_FILE_BASE_DIR, 'test_file_small.txt')
CUSTOM_METADATA = os.path.join(COMMANDS_FILE_BASE_DIR, 'custom_metadata.json')
INVALID_METADATA = os.path.join(COMMANDS_FILE_BASE_DIR,
                                'invalid_metadata.json')


def test_file_upload(mock_cli, mock_transfer_log):
    # Should not raise errors
    metadata = mock_cli.upload(EMPTY_TEST_FILE, 'my_folder')
    assert set(metadata['new_metadata']) == {'files', 'dc', 'project_metadata'}
    assert metadata['files_modified'] is True
    assert metadata['metadata_modified'] is True
    assert metadata['protocol'] == 'globus'
    assert mock_cli.ingest_entry.called
    # This is a nice way to ensure the transfer was initiated
    assert mock_transfer_log.called


def test_dir_upload(mock_cli, mock_transfer_log):
    # Should not raise errors
    metadata = mock_cli.upload(MULTI_FILE_DIR, 'my_folder')['new_metadata']
    assert set(metadata) == {'files', 'dc', 'project_metadata'}
    assert len(metadata['files']) == 4
    expected_paths = [
        'my_folder/multi_file/text_metadata.txt',
        'my_folder/multi_file/folder/tsv1.tsv',
        'my_folder/multi_file/folder/tinyimage.png',
        'my_folder/multi_file/folder/folder2/tsv2.tsv',
    ]
    expected_urls = [mock_cli.get_globus_http_url(u) for u in expected_paths]
    urls = [f['url'] for f in metadata['files']]
    for url in urls:
        assert url in expected_urls


def test_upload_without_destination(mock_cli):
    with pytest.raises(exc.NoDestinationProvided):
        mock_cli.upload(EMPTY_TEST_FILE, None)


def test_upload_to_nonexistant_dir(mock_cli, mock_transfer_error):
    mock_transfer_error.code = 'ClientError.NotFound'
    mock_cli.ls = Mock(side_effect=globus_sdk.exc.TransferAPIError)
    with pytest.raises(exc.DirectoryDoesNotExist):
        mock_cli.upload(EMPTY_TEST_FILE, 'my_folder')


def test_upload_unexpected_ls_error(mock_cli, mock_transfer_error):
    mock_transfer_error.code = 'UnexpectedError'
    mock_cli.ls = Mock(side_effect=globus_sdk.exc.TransferAPIError)
    with pytest.raises(exc.GlobusTransferError):
        mock_cli.upload(EMPTY_TEST_FILE, 'my_folder')


def test_upload_with_custom_metadata(mock_cli, mock_transfer_log):
    cust_meta = {'custom_key': 'custom_value'}
    stats = mock_cli.upload(EMPTY_TEST_FILE, 'my_folder', metadata=cust_meta)
    meta = stats['new_metadata']
    assert 'custom_key' in meta['project_metadata']
    assert meta['project_metadata']['custom_key'] == 'custom_value'


def test_upload_analyze_error(mock_cli, monkeypatch):
    mock_exc = Mock(side_effect=AnalysisException('fail!', None))
    monkeypatch.setattr(analysis, 'analyze_dataframe', mock_exc)
    with pytest.raises(exc.AnalysisException):
        mock_cli.upload(EMPTY_TEST_FILE, 'my_folder')


def test_upload_validation_error(mock_cli, mock_transfer_log):
    invalid_m = {'formats': [1234]}
    with pytest.raises(jsonschema.exceptions.ValidationError):
        mock_cli.upload(EMPTY_TEST_FILE, 'my_folder', metadata=invalid_m)


def test_no_update_needed(mock_cli, mock_transfer_log):
    url = mock_cli.get_globus_http_url(os.path.basename(EMPTY_TEST_FILE))
    meta = scrape_metadata(EMPTY_TEST_FILE, url, mock_cli.profile, 'foo')
    mock_cli.get_search_entry.return_value = meta
    mock_cli.upload(EMPTY_TEST_FILE, '/', update=True)
    assert not mock_cli.ingest_entry.called
    assert not mock_transfer_log.called


def test_upload_record_exists(mock_cli):
    url = mock_cli.get_globus_http_url('my_folder/test_file_zero_length.txt')
    meta = scrape_metadata(EMPTY_TEST_FILE, url, mock_cli.profile, 'foo')
    mock_cli.get_search_entry.return_value = meta
    with pytest.raises(exc.RecordExists):
        mock_cli.upload(SMALL_TEST_FILE, 'my_folder')


def test_upload_dry_run(mock_cli):
    stats = mock_cli.upload(SMALL_TEST_FILE, 'my_folder', dry_run=True)
    assert not stats['ingest']
    assert not stats['upload']
    assert stats['files_modified'] is True
    assert stats['metadata_modified'] is True
    assert stats['protocol'] == 'globus'
    assert stats['version'] is None
    assert stats['record_exists'] is False
    assert stats['new_version'] == '1'


def test_dataframe_up_to_date(mock_cli, mock_transfer_log):
    """Update metadata but not the actual file"""
    with open(EMTPY_TEST_FILE_META) as f:
        mock_cli.get_search_entry.return_value = json.load(f)
    new_meta = {"custom_metadata_key": "custom_metadata_value"}
    mock_cli.upload(EMPTY_TEST_FILE, '/', metadata=new_meta, update=True)
    assert not globus_sdk.TransferData.called


def test_upload_local_endpoint_not_set(mock_cli, mock_profile):

    mock_cli.profile.save_option('local_endpoint', None, section='profile')
    with pytest.raises(exc.NoLocalEndpointSet):
        mock_cli.upload(SMALL_TEST_FILE, 'my_folder', globus=True)


def test_upload_gcp_log(mock_cli, mock_transfer_log):
    mock_cli.get_search_entry.return_value = {}
    mock_cli.get_transfer_client().submit_transfer.return_value = {}
    mock_cli.upload(SMALL_TEST_FILE, 'my_folder', globus=True)
    assert mock_transfer_log.called

import os
from pilot.search import (update_metadata, scrape_metadata,
                          get_files, get_subdir_paths,
                          carryover_old_file_metadata)
from tests.unit.mocks import ANALYSIS_FILE_BASE_DIR, MULTI_FILE_DIR

MIXED_FILE = os.path.join(ANALYSIS_FILE_BASE_DIR, 'mixed.tsv')
NUMBERS_FILE = os.path.join(ANALYSIS_FILE_BASE_DIR, 'numbers.tsv')


def test_scrape_metadata(mock_cli, mock_profile):
    meta = scrape_metadata(MIXED_FILE, 'https://foo.com', mock_cli)
    dc_content = ['titles', 'creators', 'subjects', 'publicationYear',
                  'publisher', 'resourceType', 'dates', 'formats', 'version']

    assert all([c in meta['dc'].keys() for c in dc_content])
    assert meta['dc']['formats'] == ['text/tab-separated-values']
    assert meta['dc']['version'] == '1'
    assert meta['dc']['creators'][0]['creatorName'] == 'Franklin, Rosalind'
    assert set(meta.keys()) == {'dc', 'files', 'project_metadata'}
    assert 'field_metadata' in meta['files'][0].keys()
    assert 'foo-project' == meta['project_metadata']['project-slug']


def test_update_metadata_new_record_w_meta(mock_cli):
    rec = scrape_metadata(MIXED_FILE, 'https://foo.com', mock_cli)
    meta = update_metadata(rec, None, {'mime_type': 'csv'})
    assert meta['dc']['formats'] == ['csv']


def test_update_metadata_new_file(mock_cli):
    old = scrape_metadata(MIXED_FILE, 'globus://foo.com', mock_cli)
    new = scrape_metadata(NUMBERS_FILE, 'globus://foo.com', mock_cli)

    meta = update_metadata(new, old, {})
    assert old['files'][0] in meta['files']
    assert new['files'][0] in meta['files']


def test_update_metadata_prev_record(mock_cli, mock_profile):
    old = scrape_metadata(MIXED_FILE, 'globus://foo.com', mock_cli)
    mock_cli.profile.name = 'Marie Curie'
    new = scrape_metadata(MIXED_FILE, 'globus://foo.com', mock_cli)

    assert new != old
    assert old['dc']['creators'][0]['creatorName'] == 'Franklin, Rosalind'

    meta = update_metadata(new, old, {})
    assert meta['dc']['creators'][0]['creatorName'] == 'Curie, Marie'
    assert meta['files'] == new['files'] == old['files']


def test_carryover_old_file_metadata_same_file():
    file1 = [{'url': 'foo.txt'}]
    assert carryover_old_file_metadata(file1, file1) == file1


def test_carryover_old_file_metadata_diff_mimetype():
    old = [{'url': 'foo.txt', 'mime_type': 'text/plain'}]
    new = [{'url': 'foo.txt'}]
    assert carryover_old_file_metadata(new, old) == old


def test_carryover_old_file_metadata_skips_attrs():
    old = [{'url': 'foo.txt', 'length': 10, 'md5': 'abc', 'sha256': 'xyz'}]
    new = [{'url': 'foo.txt', 'length': 20, 'md5': 'def'}]
    assert carryover_old_file_metadata(new, old) == new


def test_carryover_old_file_metadata_does_not_overwrite():
    old = [{'url': 'foo.txt', 'mime_type': 'text/csv'}]
    new = [{'url': 'foo.txt', 'mime_type': 'text/plain'}]
    assert carryover_old_file_metadata(new, old) == new


def test_carryover_old_file_metadata_with_mix():
    old = [{'url': 'foo.txt', 'length': 10, 'md5': 'abc', 'sha256': 'xyz',
            'custom_attr': 'foo', 'extra_attr': 'bar'}]
    new = [{'url': 'foo.txt', 'length': 20, 'md5': 'def',
            'custom_attr': 'foo'}]
    expected = [{'url': 'foo.txt', 'length': 20, 'md5': 'def',
                 'custom_attr': 'foo', 'extra_attr': 'bar'}]
    assert carryover_old_file_metadata(new, old) == expected


def test_carryover_unrelated_files():
    old = [{'url': 'foo'}]
    new = [{'url': 'bar'}]
    assert carryover_old_file_metadata(new, old) == new + old


def test_update_file_version(mock_cli, mock_profile):

    ver_one = scrape_metadata(MIXED_FILE, 'globus://foo.com', mock_cli)
    ver_two = scrape_metadata(NUMBERS_FILE, 'globus://foo.com', mock_cli)
    assert ver_one['dc']['version'] == '1'
    assert ver_two['dc']['version'] == '1'
    # Pretend 'NUMBERS_FILE' is an updated version of MIXED_FILE
    updated = update_metadata(ver_two, ver_one, {})
    assert updated['dc']['version'] == '2'
    # Pretend we switched back
    updated_3 = update_metadata(ver_one, updated, {})
    assert updated_3['dc']['version'] == '3'
    # Check re-updating does not bump version
    updated_3 = update_metadata(ver_one, updated, {})
    assert updated_3['dc']['version'] == '3'


def test_get_files():
    files = get_files(MULTI_FILE_DIR)
    assert len(files) == 4
    one_file = get_files(MIXED_FILE)
    assert len(one_file) == 1


def test_get_subdir_paths_on_dir():
    for local_path, remote_path in get_subdir_paths(MULTI_FILE_DIR):
        assert MULTI_FILE_DIR in local_path
        folder_name = os.path.basename(MULTI_FILE_DIR)
        assert remote_path.startswith(folder_name)


def test_get_subdir_paths_on_file():
    for local_path, remote_path in get_subdir_paths(MIXED_FILE):
        assert os.path.basename(local_path) == remote_path

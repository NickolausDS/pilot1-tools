import pytest
from pilot.exc import NoEntryToUpdate, ContentMismatch

MIN_FIELDS = {
    'dataframe_type': 'Matrix',
    'data_type': 'Metadata',
    'mime_type': 'text/tab-separated-values'
}


def test_update_entry_metadata(mock_pc_w_entry):
    info = mock_pc_w_entry.update_entry('foo/bar', MIN_FIELDS)
    assert info['updated_entry']
    assert info['pre_existing_record']
    assert not info['dataframe_changed']
    assert info['version'] == '1'


def test_update_entry_content(mock_pc_w_entry, numbers_tsv):
    # numbers_csv is a different file, making this 'full' update
    info = mock_pc_w_entry.update_entry('foo/bar', MIN_FIELDS,
                                        dataframe=numbers_tsv,
                                        update_content=True)
    assert info['updated_entry']
    assert info['pre_existing_record']
    assert info['dataframe_changed']
    assert info['version'] == '2'


def test_update_entry_dry_run(mock_pc_w_entry, numbers_tsv):
    info = mock_pc_w_entry.update_entry('foo/bar', MIN_FIELDS,
                                        dataframe=numbers_tsv,
                                        dry_run=True,
                                        update_content=True)
    assert not info['updated_entry']
    assert info['pre_existing_record']
    assert info['dataframe_changed']
    assert info['version'] == '2'


def test_no_record_to_update_raises_error(mock_auth_pilot_cli):
    with pytest.raises(NoEntryToUpdate):
        mock_auth_pilot_cli.update_entry('foo/bar', {})


def test_update_modified_entry_raises_error(mock_pc_w_entry,
                                            numbers_tsv):
    with pytest.raises(ContentMismatch):
        mock_pc_w_entry.update_entry(
            'foo/bar', MIN_FIELDS, dataframe=numbers_tsv
        )


def test_update_existing_entry(mock_pc_w_entry):
    info = mock_pc_w_entry.update_entry('foo/bar', MIN_FIELDS)
    assert info['updated_entry']
    assert not info['dataframe_changed']
    assert info['version'] == '1'

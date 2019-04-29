import pytest
import os
import copy
import globus_sdk
from unittest.mock import Mock
from .mocks import (MemoryStorage, MOCK_TOKEN_SET, GlobusTransferTaskResponse,
                    ANALYSIS_FILE_BASE_DIR)


from pilot.client import PilotClient
import pilot
from pilot.search import scrape_metadata


@pytest.fixture
def mem_storage():
    return MemoryStorage()


@pytest.fixture
def mock_tokens():
    return copy.deepcopy(MOCK_TOKEN_SET)


@pytest.fixture
def mock_config(monkeypatch):

    class MockConfig(pilot.config.Config):
        data = {
            'profile': {'name': 'John Doe'}
        }

        def save(self, data):
            self.data = {str(k): v for k, v in data.items()}

        def load(self):
            return self.data

    mc = MockConfig()
    monkeypatch.setattr(pilot.config, 'config', mc)
    return mc


@pytest.fixture
def mixed_tsv():
    return os.path.join(ANALYSIS_FILE_BASE_DIR, 'mixed.tsv')


@pytest.fixture
def numbers_tsv():
    return os.path.join(ANALYSIS_FILE_BASE_DIR, 'numbers.tsv')


@pytest.fixture
def strings_tsv():
    return os.path.join(ANALYSIS_FILE_BASE_DIR, 'strings.tsv')


@pytest.fixture
def mock_transfer_client(monkeypatch):
    st = Mock()
    monkeypatch.setattr(globus_sdk.TransferClient, 'submit_transfer', st)
    st.return_value = GlobusTransferTaskResponse()
    monkeypatch.setattr(globus_sdk, 'TransferData', Mock())
    return st


@pytest.fixture
def mock_auth_pilot_cli(mock_transfer_client, mock_config):
    """
    Returns a mock logged in pilot client. Storage is mocked with a custom
    object, so this does behave slightly differently than the real client.
    All methods that reach out to remote resources are mocked, you need to
    re-mock them to return the test data you want.
    """
    pc = PilotClient()
    pc.token_storage = MemoryStorage()
    pc.token_storage.tokens = MOCK_TOKEN_SET
    pc.BASE_DIR = 'prod'
    pc.ENDPOINT = 'endpoint'
    pc.SEARCH_INDEX = 'search_index'
    pc.SEARCH_INDEX_TEST = 'search_index_test'
    pc.upload = Mock()
    pc.ingest_entry = Mock()
    pc.get_search_entry = Mock(return_value=None)
    pc.ls = Mock()
    # Sanity. This *should* always return True, but will fail if we update
    # tokens at a later time.
    assert pc.is_logged_in()
    return pc


@pytest.fixture
def mock_pc_w_entry(mock_auth_pilot_cli, mixed_tsv):
    entry_json = scrape_metadata(mixed_tsv, None, {})
    mock_auth_pilot_cli.get_search_entry.return_value = entry_json
    return mock_auth_pilot_cli


@pytest.fixture
def mock_command_pilot_cli(mock_auth_pilot_cli, monkeypatch):
    mock_func = Mock()
    mock_func.return_value = mock_auth_pilot_cli
    monkeypatch.setattr(pilot.commands, 'get_pilot_client', mock_func)
    return mock_auth_pilot_cli

import pytest
import os
import copy
import globus_sdk
from unittest.mock import Mock
from .mocks import (MemoryStorage, MOCK_TOKEN_SET, GlobusTransferTaskResponse,
                    ANALYSIS_FILE_BASE_DIR)

from pilot.client import PilotClient
import pilot


@pytest.fixture
def mem_storage():
    return MemoryStorage()


@pytest.fixture
def mock_tokens():
    return copy.deepcopy(MOCK_TOKEN_SET)


@pytest.fixture
def mock_config(monkeypatch):

    class MockConfig(pilot.config.Config):
        data = {}

        def save(self, data):
            self.data = {str(k): v for k, v in data.items()}

        def load(self):
            return self.data

    mc = MockConfig()
    monkeypatch.setattr(pilot.config, 'config', mc)
    return mc


@pytest.fixture
def simple_tsv():
    return os.path.join(ANALYSIS_FILE_BASE_DIR, 'simple.tsv')


@pytest.fixture
def mock_transfer_client(monkeypatch):
    st = Mock()
    monkeypatch.setattr(globus_sdk.TransferClient, 'submit_transfer', st)
    st.return_value = GlobusTransferTaskResponse()
    monkeypatch.setattr(globus_sdk, 'TransferData', Mock())
    return st


@pytest.fixture
def mock_auth_pilot_cli(mock_transfer_client):
    """
    Returns a mock logged in pilot client. Storage is mocked with a custom
    object, so this does behave slightly differently than the real client.
    All methods that reach out to remote resources are mocked, you need to
    re-mock them to return the test data you want.
    """
    pc = PilotClient()
    pc.token_storage = MemoryStorage()
    pc.token_storage.tokens = MOCK_TOKEN_SET
    pc.upload = Mock()
    pc.ingest_entry = Mock()
    pc.get_search_entry = Mock()
    pc.ls = Mock()
    # Sanity. This *should* always return True, but will fail if we update
    # tokens at a later time.
    assert pc.is_logged_in()
    return pc


@pytest.fixture
def mock_command_pilot_cli(mock_auth_pilot_cli, monkeypatch):
    mock_func = Mock()
    mock_func.return_value = mock_auth_pilot_cli
    monkeypatch.setattr(pilot.commands, 'get_pilot_client', mock_func)
    return mock_auth_pilot_cli

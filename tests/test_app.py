import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from unittest.mock import patch, MagicMock

# Mock redis before importing app
mock_redis = MagicMock()
mock_redis.ping.return_value = True
mock_redis.get.return_value = None
mock_redis.set.return_value = True
mock_redis.exists.return_value = False
mock_redis.incr.return_value = 1

with patch('redis.Redis', return_value=mock_redis):
    from app import app as flask_app


@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as client:
        yield client


def test_home_page(client):
    """Test that home page loads successfully."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'LinkSnip' in response.data


def test_health_check(client):
    """Test /health endpoint returns healthy."""
    mock_redis.ping.return_value = True
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'


def test_shorten_valid_url(client):
    """Test shortening a valid URL returns a short code."""
    mock_redis.exists.return_value = False
    mock_redis.get.return_value = None
    response = client.post('/api/shorten',
                           json={'url': 'https://www.example.com'},
                           content_type='application/json')
    assert response.status_code == 200
    data = response.get_json()
    assert 'short_url' in data
    assert 'code' in data
    assert len(data['code']) == 6


def test_shorten_missing_url(client):
    """Test shortening with missing URL returns 400."""
    response = client.post('/api/shorten',
                           json={},
                           content_type='application/json')
    assert response.status_code == 400


def test_shorten_invalid_url(client):
    """Test shortening an invalid URL returns 400."""
    response = client.post('/api/shorten',
                           json={'url': 'not-a-valid-url'},
                           content_type='application/json')
    assert response.status_code == 400


def test_redirect_not_found(client):
    """Test redirect for non-existent code returns 404."""
    mock_redis.get.return_value = None
    response = client.get('/nonexistent')
    assert response.status_code == 404


def test_redirect_valid_code(client):
    """Test redirect for valid code follows the stored URL."""
    mock_redis.get.return_value = 'https://www.example.com'
    response = client.get('/abc123')
    assert response.status_code in [301, 302]


def test_stats_endpoint(client):
    """Test /api/stats returns expected fields."""
    mock_redis.get.side_effect = lambda key: b'5' if 'total' in key else None
    response = client.get('/api/stats')
    assert response.status_code == 200
    data = response.get_json()
    assert 'total_links' in data
    assert 'total_clicks' in data

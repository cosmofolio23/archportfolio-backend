"""
Authentication & Authorization Tests for CosmoFolio
Phase 1: Task 1.8 - Verify Firebase integration and RLS policies
"""

import pytest
import os
from uuid import uuid4
from datetime import datetime
import json
from fastapi.testclient import TestClient
from dotenv import load_dotenv

load_dotenv()

# These tests verify:
# 1. Firebase token validation
# 2. Token refresh mechanism
# 3. RLS policies enforcement
# 4. Access control (403 on unauthorized)
# 5. Public portfolio access without auth
# 6. Token expiration handling

class TestAuthenticationFlow:
    """Test Firebase authentication flow"""

    def test_create_portfolio_requires_auth(self, client: TestClient):
        """Verify portfolio creation requires valid auth token"""
        response = client.post(
            "/api/portfolios",
            json={
                "title": "Test Portfolio",
                "architect_name": "Test Architect",
                "page_size": "a4",
                "page_orientation": "portrait",
                "margins": "standard"
            }
        )
        assert response.status_code == 403, "Should require authentication"

    def test_valid_firebase_token_accepted(self, client: TestClient, valid_token: str):
        """Verify valid Firebase tokens are accepted"""
        response = client.post(
            "/api/portfolios",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={
                "title": "Test Portfolio",
                "architect_name": "Test Architect",
                "page_size": "a4",
                "page_orientation": "portrait",
                "margins": "standard"
            }
        )
        assert response.status_code == 200, f"Valid token should be accepted, got {response.status_code}"
        assert response.json()["id"] is not None

    def test_invalid_token_rejected(self, client: TestClient):
        """Verify invalid tokens are rejected"""
        response = client.post(
            "/api/portfolios",
            headers={"Authorization": "Bearer invalid_token_12345"},
            json={
                "title": "Test Portfolio",
                "architect_name": "Test Architect",
                "page_size": "a4",
                "page_orientation": "portrait",
                "margins": "standard"
            }
        )
        assert response.status_code == 401, "Invalid token should be rejected"

    def test_expired_token_rejected(self, client: TestClient, expired_token: str):
        """Verify expired tokens are rejected"""
        response = client.post(
            "/api/portfolios",
            headers={"Authorization": f"Bearer {expired_token}"},
            json={
                "title": "Test Portfolio",
                "architect_name": "Test Architect",
                "page_size": "a4",
                "page_orientation": "portrait",
                "margins": "standard"
            }
        )
        assert response.status_code == 401, "Expired token should be rejected"

    def test_missing_bearer_prefix(self, client: TestClient, valid_token: str):
        """Verify token must have Bearer prefix"""
        response = client.post(
            "/api/portfolios",
            headers={"Authorization": valid_token},  # Missing "Bearer " prefix
            json={
                "title": "Test Portfolio",
                "architect_name": "Test Architect",
                "page_size": "a4",
                "page_orientation": "portrait",
                "margins": "standard"
            }
        )
        assert response.status_code == 403, "Bearer prefix is required"


class TestAuthorizationRLS:
    """Test Row-Level Security policies"""

    def test_user_cannot_access_other_portfolios(
        self,
        client: TestClient,
        user1_token: str,
        user2_token: str
    ):
        """Verify User1 cannot access User2's portfolios (RLS)"""
        # Create portfolio as User 1
        response = client.post(
            "/api/portfolios",
            headers={"Authorization": f"Bearer {user1_token}"},
            json={
                "title": "User1 Portfolio",
                "architect_name": "User 1",
                "page_size": "a4",
                "page_orientation": "portrait",
                "margins": "standard"
            }
        )
        assert response.status_code == 200
        portfolio_id = response.json()["id"]

        # Try to access as User 2
        response = client.get(
            f"/api/portfolios/{portfolio_id}",
            headers={"Authorization": f"Bearer {user2_token}"}
        )
        assert response.status_code == 403, "User2 should not access User1's portfolio"

    def test_user_cannot_update_other_portfolios(
        self,
        client: TestClient,
        user1_token: str,
        user2_token: str
    ):
        """Verify User1 cannot update User2's portfolios"""
        # Create portfolio as User 1
        response = client.post(
            "/api/portfolios",
            headers={"Authorization": f"Bearer {user1_token}"},
            json={
                "title": "User1 Portfolio",
                "architect_name": "User 1",
                "page_size": "a4",
                "page_orientation": "portrait",
                "margins": "standard"
            }
        )
        portfolio_id = response.json()["id"]

        # Try to update as User 2
        response = client.put(
            f"/api/portfolios/{portfolio_id}",
            headers={"Authorization": f"Bearer {user2_token}"},
            json={
                "title": "Hacked Title",
                "architect_name": "User 1",
                "page_size": "a4",
                "page_orientation": "portrait",
                "margins": "standard"
            }
        )
        assert response.status_code == 403, "User2 should not modify User1's portfolio"

    def test_user_cannot_delete_other_portfolios(
        self,
        client: TestClient,
        user1_token: str,
        user2_token: str
    ):
        """Verify User1 cannot delete User2's portfolios"""
        # Create portfolio as User 1
        response = client.post(
            "/api/portfolios",
            headers={"Authorization": f"Bearer {user1_token}"},
            json={
                "title": "User1 Portfolio",
                "architect_name": "User 1",
                "page_size": "a4",
                "page_orientation": "portrait",
                "margins": "standard"
            }
        )
        portfolio_id = response.json()["id"]

        # Try to delete as User 2
        response = client.delete(
            f"/api/portfolios/{portfolio_id}",
            headers={"Authorization": f"Bearer {user2_token}"}
        )
        assert response.status_code == 403, "User2 should not delete User1's portfolio"

    def test_user_can_access_published_portfolio(
        self,
        client: TestClient,
        user1_token: str,
        user2_token: str
    ):
        """Verify users can access published portfolios (even without ownership)"""
        # Create and publish portfolio as User 1
        response = client.post(
            "/api/portfolios",
            headers={"Authorization": f"Bearer {user1_token}"},
            json={
                "title": "Public Portfolio",
                "architect_name": "User 1",
                "page_size": "a4",
                "page_orientation": "portrait",
                "margins": "standard"
            }
        )
        portfolio_id = response.json()["id"]

        # Publish it
        client.put(
            f"/api/portfolios/{portfolio_id}",
            headers={"Authorization": f"Bearer {user1_token}"},
            json={
                "title": "Public Portfolio",
                "architect_name": "User 1",
                "page_size": "a4",
                "page_orientation": "portrait",
                "margins": "standard",
                "is_published": True
            }
        )

        # User 2 should see it
        response = client.get(
            f"/api/portfolios/{portfolio_id}",
            headers={"Authorization": f"Bearer {user2_token}"}
        )
        assert response.status_code == 200, "Published portfolio should be readable by others"


class TestPublicAccess:
    """Test public portfolio access without authentication"""

    def test_public_portfolio_view_without_auth(
        self,
        client: TestClient,
        user1_token: str
    ):
        """Verify published portfolios are viewable without auth"""
        # Create portfolio as User 1
        response = client.post(
            "/api/portfolios",
            headers={"Authorization": f"Bearer {user1_token}"},
            json={
                "title": "Public Portfolio",
                "architect_name": "User 1",
                "page_size": "a4",
                "page_orientation": "portrait",
                "margins": "standard"
            }
        )
        portfolio_id = response.json()["id"]

        # Access public endpoint without auth
        response = client.get(f"/api/portfolios/{portfolio_id}/public")
        assert response.status_code == 404, "Unpublished portfolio should not be accessible"

        # Publish it
        client.put(
            f"/api/portfolios/{portfolio_id}",
            headers={"Authorization": f"Bearer {user1_token}"},
            json={"is_published": True}
        )

        # Now should be accessible without auth
        response = client.get(f"/api/portfolios/{portfolio_id}/public")
        assert response.status_code == 200, "Published portfolio should be public"

    def test_public_view_increments_view_count(
        self,
        client: TestClient,
        user1_token: str
    ):
        """Verify public portfolio views increment counter"""
        # Create and publish portfolio
        response = client.post(
            "/api/portfolios",
            headers={"Authorization": f"Bearer {user1_token}"},
            json={
                "title": "Public Portfolio",
                "architect_name": "User 1",
                "page_size": "a4",
                "page_orientation": "portrait",
                "margins": "standard"
            }
        )
        portfolio_id = response.json()["id"]

        # Publish it (assuming we add is_published field)
        client.put(
            f"/api/portfolios/{portfolio_id}",
            headers={"Authorization": f"Bearer {user1_token}"},
            json={"is_published": True}
        )

        # View 3 times without auth
        for _ in range(3):
            client.get(f"/api/portfolios/{portfolio_id}/public")

        # Check view count
        response = client.get(
            f"/api/portfolios/{portfolio_id}",
            headers={"Authorization": f"Bearer {user1_token}"}
        )
        assert response.json()["view_count"] == 3, "View count should increment"


class TestTokenRefresh:
    """Test token refresh mechanism"""

    def test_token_refresh_endpoint_exists(self, client: TestClient):
        """Verify token refresh endpoint is available"""
        # This assumes /auth/refresh endpoint
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": "dummy_token"}
        )
        # Should not be 404 (endpoint exists)
        assert response.status_code != 404

    def test_valid_refresh_token_returns_new_token(
        self,
        client: TestClient,
        valid_refresh_token: str
    ):
        """Verify refresh token generates new access token"""
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": valid_refresh_token}
        )
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_invalid_refresh_token_rejected(self, client: TestClient):
        """Verify invalid refresh tokens are rejected"""
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": "invalid_refresh_token"}
        )
        assert response.status_code == 401


class TestErrorResponses:
    """Test error response standardization"""

    def test_401_on_missing_token(self, client: TestClient):
        """Verify 401 on missing auth token"""
        response = client.get("/api/portfolios")
        assert response.status_code == 401
        assert "detail" in response.json()

    def test_403_on_unauthorized_access(
        self,
        client: TestClient,
        user1_token: str,
        user2_token: str
    ):
        """Verify 403 on access denied"""
        # Create portfolio as User 1
        response = client.post(
            "/api/portfolios",
            headers={"Authorization": f"Bearer {user1_token}"},
            json={
                "title": "User1 Portfolio",
                "architect_name": "User 1",
                "page_size": "a4",
                "page_orientation": "portrait",
                "margins": "standard"
            }
        )
        portfolio_id = response.json()["id"]

        # Try to access as User 2
        response = client.get(
            f"/api/portfolios/{portfolio_id}",
            headers={"Authorization": f"Bearer {user2_token}"}
        )
        assert response.status_code == 403
        assert "Access denied" in response.json()["detail"]

    def test_404_on_not_found(self, client: TestClient, valid_token: str):
        """Verify 404 on missing resource"""
        response = client.get(
            f"/api/portfolios/{uuid4()}",
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_400_on_bad_request(self, client: TestClient, valid_token: str):
        """Verify 400 on invalid request data"""
        response = client.post(
            "/api/portfolios",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={
                "title": "Test",
                # Missing required fields
            }
        )
        assert response.status_code == 400


# ==================== FIXTURES ====================

@pytest.fixture
def valid_token() -> str:
    """Valid Firebase token fixture"""
    # In real tests, this would be generated from Firebase test SDK
    return os.getenv("TEST_VALID_TOKEN", "test_valid_token_12345")

@pytest.fixture
def expired_token() -> str:
    """Expired Firebase token fixture"""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJleHAiOjE1MTYyMzIwMjJ9"

@pytest.fixture
def user1_token() -> str:
    """User 1 Firebase token fixture"""
    return os.getenv("TEST_USER1_TOKEN", "test_user1_token_12345")

@pytest.fixture
def user2_token() -> str:
    """User 2 Firebase token fixture"""
    return os.getenv("TEST_USER2_TOKEN", "test_user2_token_67890")

@pytest.fixture
def valid_refresh_token() -> str:
    """Valid refresh token fixture"""
    return os.getenv("TEST_REFRESH_TOKEN", "test_refresh_token_12345")

@pytest.fixture
def client() -> TestClient:
    """Test client fixture"""
    # Import after fixtures are defined to avoid circular imports
    from main import app
    return TestClient(app)

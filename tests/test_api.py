import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """
    Fixture that provides a TestClient with isolated activity state.
    Resets activities to a known state before each test to avoid interference.
    """
    # Save original activities
    original_activities = activities.copy()
    
    # Reset activities to initial test state
    activities.clear()
    activities.update({
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu"]
        },
    })
    
    # Create and yield the test client
    test_client = TestClient(app)
    yield test_client
    
    # Restore original activities after test
    activities.clear()
    activities.update(original_activities)


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client):
        """Should return all activities with correct structure"""
        # Arrange
        # (Pre-loaded activities via fixture)
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert data["Chess Club"]["description"] == "Learn strategies and compete in chess tournaments"
        assert data["Chess Club"]["max_participants"] == 12
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
    
    def test_get_activities_has_correct_fields(self, client):
        """Should return activities with all required fields"""
        # Arrange
        # (Pre-loaded activities via fixture)
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        for activity_name, activity_details in data.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_new_participant_success(self, client):
        """Should successfully sign up a new participant"""
        # Arrange
        email = "newstudent@mergington.edu"
        activity = "Chess Club"
        
        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert "Signed up" in data["message"]
        assert email in data["message"]
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data[activity]["participants"]
    
    def test_signup_duplicate_participant_fails(self, client):
        """Should reject duplicate signup with 400 error"""
        # Arrange
        email = "michael@mergington.edu"
        activity = "Chess Club"
        
        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        data = response.json()
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in data["detail"].lower()
    
    def test_signup_nonexistent_activity_fails(self, client):
        """Should return 404 for non-existent activity"""
        # Arrange
        email = "student@mergington.edu"
        activity = "Nonexistent Club"
        
        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        data = response.json()
        
        # Assert
        assert response.status_code == 404
        assert "not found" in data["detail"].lower()
    
    def test_signup_multiple_different_participants(self, client):
        """Should allow multiple different participants to sign up"""
        # Arrange
        email1 = "student1@mergington.edu"
        email2 = "student2@mergington.edu"
        activity = "Programming Class"
        
        # Act
        response1 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email1}
        )
        response2 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email2}
        )
        
        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        participants = activities_data[activity]["participants"]
        assert email1 in participants
        assert email2 in participants


class TestUnregister:
    """Tests for DELETE /activities/{activity_name}/signup endpoint"""
    
    def test_unregister_existing_participant_success(self, client):
        """Should successfully unregister an existing participant"""
        # Arrange
        email = "michael@mergington.edu"
        activity = "Chess Club"
        
        # Act
        response = client.delete(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert "Unregistered" in data["message"]
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email not in activities_data[activity]["participants"]
    
    def test_unregister_nonexistent_participant_fails(self, client):
        """Should return 400 when trying to unregister a non-registered participant"""
        # Arrange
        email = "notregistered@mergington.edu"
        activity = "Chess Club"
        
        # Act
        response = client.delete(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        data = response.json()
        
        # Assert
        assert response.status_code == 400
        assert "not signed up" in data["detail"].lower()
    
    def test_unregister_from_nonexistent_activity_fails(self, client):
        """Should return 404 when trying to unregister from non-existent activity"""
        # Arrange
        email = "michael@mergington.edu"
        activity = "Nonexistent Club"
        
        # Act
        response = client.delete(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        data = response.json()
        
        # Assert
        assert response.status_code == 404
        assert "not found" in data["detail"].lower()
    
    def test_unregister_then_rejoin_works(self, client):
        """Should allow a participant to rejoin after unregistering"""
        # Arrange
        email = "michael@mergington.edu"
        activity = "Chess Club"
        
        # Act - Unregister
        response1 = client.delete(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Assert - Verify removed
        assert response1.status_code == 200
        activities_response1 = client.get("/activities")
        assert email not in activities_response1.json()[activity]["participants"]
        
        # Act - Sign up again
        response2 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Assert - Verify re-added
        assert response2.status_code == 200
        activities_response2 = client.get("/activities")
        assert email in activities_response2.json()[activity]["participants"]


class TestIntegration:
    """Integration tests for complete signup/unregister flow"""
    
    def test_complete_signup_flow(self, client):
        """Test complete flow: get activities -> signup -> verify"""
        # Arrange
        email = "testuser@mergington.edu"
        activity = "Chess Club"
        
        response1 = client.get("/activities")
        initial_count = len(response1.json()[activity]["participants"])
        
        # Act - Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Act - Get updated activities
        response2 = client.get("/activities")
        activities_data = response2.json()
        final_count = len(activities_data[activity]["participants"])
        final_participants = activities_data[activity]["participants"]
        
        # Assert
        assert signup_response.status_code == 200
        assert final_count == initial_count + 1
        assert email in final_participants

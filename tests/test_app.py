"""
Tests for the Mergington High School Activities API
"""
import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to a known state before each test"""
    # Clear all participants from all activities
    for activity in activities.values():
        activity["participants"] = []
    
    # Set some initial participants for testing
    activities["Chess Club"]["participants"] = ["michael@mergington.edu", "daniel@mergington.edu"]
    activities["Programming Class"]["participants"] = ["emma@mergington.edu", "sophia@mergington.edu"]
    activities["Gym Class"]["participants"] = ["john@mergington.edu", "olivia@mergington.edu"]
    
    yield
    
    # Reset again after test
    for activity in activities.values():
        activity["participants"] = []
    activities["Chess Club"]["participants"] = ["michael@mergington.edu", "daniel@mergington.edu"]
    activities["Programming Class"]["participants"] = ["emma@mergington.edu", "sophia@mergington.edu"]
    activities["Gym Class"]["participants"] = ["john@mergington.edu", "olivia@mergington.edu"]


class TestRootEndpoint:
    """Test the root endpoint"""
    
    def test_root_redirects_to_static(self, client):
        """Test that root endpoint redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]


class TestActivitiesEndpoint:
    """Test the activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that activities endpoint returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        
        # Verify all expected activities are present
        assert "Basketball Team" in data
        assert "Soccer Club" in data
        assert "Art Club" in data
        assert "Drama Club" in data
        assert "Debate Team" in data
        assert "Math Club" in data
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
    
    def test_activity_structure(self, client, reset_activities):
        """Test that each activity has the expected structure"""
        response = client.get("/activities")
        data = response.json()
        
        activity = data["Basketball Team"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)
    
    def test_activities_have_participants(self, client, reset_activities):
        """Test that activities show their participants"""
        response = client.get("/activities")
        data = response.json()
        
        # Check that Chess Club has the initial participants
        assert len(data["Chess Club"]["participants"]) == 2
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in data["Chess Club"]["participants"]


class TestSignupEndpoint:
    """Test the signup endpoint"""
    
    def test_signup_for_activity_success(self, client, reset_activities):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Basketball Team/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert "newstudent@mergington.edu" in data["message"]
        
        # Verify the participant was added
        assert "newstudent@mergington.edu" in activities["Basketball Team"]["participants"]
    
    def test_signup_for_nonexistent_activity(self, client, reset_activities):
        """Test signup for an activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent Activity/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_duplicate_not_allowed(self, client, reset_activities):
        """Test that a student can't sign up twice for the same activity"""
        email = "duplicate@mergington.edu"
        
        # First signup should succeed
        response1 = client.post(
            "/activities/Basketball Team/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Second signup should fail
        response2 = client.post(
            "/activities/Basketball Team/signup",
            params={"email": email}
        )
        assert response2.status_code == 400
        data = response2.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_multiple_students(self, client, reset_activities):
        """Test that multiple different students can sign up"""
        students = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        
        for student in students:
            response = client.post(
                "/activities/Art Club/signup",
                params={"email": student}
            )
            assert response.status_code == 200
        
        # Verify all students are in the activity
        assert len(activities["Art Club"]["participants"]) == 3
        for student in students:
            assert student in activities["Art Club"]["participants"]


class TestUnregisterEndpoint:
    """Test the unregister endpoint"""
    
    def test_unregister_success(self, client, reset_activities):
        """Test successful unregistration from an activity"""
        email = "michael@mergington.edu"
        
        # Verify the student is in the activity
        assert email in activities["Chess Club"]["participants"]
        
        # Unregister
        response = client.post(
            "/activities/Chess Club/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        
        # Verify the student was removed
        assert email not in activities["Chess Club"]["participants"]
    
    def test_unregister_nonexistent_activity(self, client, reset_activities):
        """Test unregistration from an activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent Activity/unregister",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_unregister_not_signed_up(self, client, reset_activities):
        """Test unregistration when student is not signed up"""
        response = client.post(
            "/activities/Basketball Team/unregister",
            params={"email": "notsigndup@mergington.edu"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]
    
    def test_unregister_multiple_students(self, client, reset_activities):
        """Test unregistering multiple students"""
        activity = "Programming Class"
        initial_count = len(activities[activity]["participants"])
        
        email1 = activities[activity]["participants"][0]
        
        response = client.post(
            f"/activities/{activity}/unregister",
            params={"email": email1}
        )
        assert response.status_code == 200
        assert len(activities[activity]["participants"]) == initial_count - 1
        assert email1 not in activities[activity]["participants"]


class TestIntegration:
    """Integration tests"""
    
    def test_signup_and_view(self, client, reset_activities):
        """Test signing up and then viewing the updated activity"""
        email = "integration@mergington.edu"
        activity = "Art Club"
        
        # Sign up
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Get activities and verify the signup
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert email in data[activity]["participants"]
    
    def test_signup_unregister_signup_again(self, client, reset_activities):
        """Test signup, unregister, and signup again"""
        email = "cycletest@mergington.edu"
        activity = "Debate Team"
        
        # First signup
        response1 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        assert email in activities[activity]["participants"]
        
        # Unregister
        response2 = client.post(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert response2.status_code == 200
        assert email not in activities[activity]["participants"]
        
        # Sign up again
        response3 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response3.status_code == 200
        assert email in activities[activity]["participants"]

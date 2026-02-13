"""
Tests for the Mergington High School Activities API.
"""
import pytest


class TestGetActivities:
    """Tests for the GET /activities endpoint."""
    
    def test_get_activities_success(self, client, reset_activities):
        """Test retrieving all activities."""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        
        # Check that we get all activities
        assert len(data) == 9
        assert "Basketball Club" in data
        assert "Tennis Team" in data
        assert "Drama Club" in data
    
    def test_get_activities_structure(self, client, reset_activities):
        """Test that activities have the correct structure."""
        response = client.get("/activities")
        data = response.json()
        
        activity = data["Basketball Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)
    
    def test_get_activities_participants(self, client, reset_activities):
        """Test that participants are returned correctly."""
        response = client.get("/activities")
        data = response.json()
        
        # Basketball Club should have james@mergington.edu
        assert "james@mergington.edu" in data["Basketball Club"]["participants"]
        
        # Drama Club should have both alex and isabella
        drama_participants = data["Drama Club"]["participants"]
        assert "alex@mergington.edu" in drama_participants
        assert "isabella@mergington.edu" in drama_participants


class TestSignupForActivity:
    """Tests for the POST /activities/{activity_name}/signup endpoint."""
    
    def test_signup_success(self, client, reset_activities):
        """Test successfully signing up for an activity."""
        response = client.post(
            "/activities/Basketball Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert "newstudent@mergington.edu" in data["message"]
    
    def test_signup_activity_not_found(self, client, reset_activities):
        """Test signing up for a non-existent activity."""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_signup_already_registered(self, client, reset_activities):
        """Test signing up when already registered."""
        response = client.post(
            "/activities/Basketball Club/signup?email=james@mergington.edu"
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_updates_participants_list(self, client, reset_activities):
        """Test that signup actually adds the participant to the list."""
        # First, sign up
        response = client.post(
            "/activities/Tennis Team/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        
        # Then retrieve activities and verify
        response = client.get("/activities")
        participants = response.json()["Tennis Team"]["participants"]
        assert "newstudent@mergington.edu" in participants
    
    def test_signup_duplicate_email_formats(self, client, reset_activities):
        """Test that signup is case-sensitive for emails."""
        # First signup
        response1 = client.post(
            "/activities/Art Studio/signup?email=student@mergington.edu"
        )
        assert response1.status_code == 200
        
        # Verify participant was added
        response = client.get("/activities")
        assert "student@mergington.edu" in response.json()["Art Studio"]["participants"]


class TestUnregisterFromActivity:
    """Tests for the DELETE /activities/{activity_name}/unregister endpoint."""
    
    def test_unregister_success(self, client, reset_activities):
        """Test successfully unregistering from an activity."""
        response = client.delete(
            "/activities/Basketball Club/unregister?email=james@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        assert "james@mergington.edu" in data["message"]
    
    def test_unregister_activity_not_found(self, client, reset_activities):
        """Test unregistering from a non-existent activity."""
        response = client.delete(
            "/activities/Nonexistent Club/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_unregister_not_registered(self, client, reset_activities):
        """Test unregistering when not registered."""
        response = client.delete(
            "/activities/Basketball Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]
    
    def test_unregister_removes_from_list(self, client, reset_activities):
        """Test that unregister actually removes the participant."""
        # First, verify they're registered
        response = client.get("/activities")
        assert "james@mergington.edu" in response.json()["Basketball Club"]["participants"]
        
        # Unregister
        response = client.delete(
            "/activities/Basketball Club/unregister?email=james@mergington.edu"
        )
        assert response.status_code == 200
        
        # Verify they're removed
        response = client.get("/activities")
        assert "james@mergington.edu" not in response.json()["Basketball Club"]["participants"]
    
    def test_unregister_does_not_affect_other_activities(self, client, reset_activities):
        """Test that unregistering doesn't affect other activities."""
        # Get initial state
        response = client.get("/activities")
        initial_drama = set(response.json()["Drama Club"]["participants"])
        
        # Unregister from different activity
        client.delete(
            "/activities/Basketball Club/unregister?email=james@mergington.edu"
        )
        
        # Verify Drama Club is unchanged
        response = client.get("/activities")
        assert set(response.json()["Drama Club"]["participants"]) == initial_drama


class TestSignupAndUnregisterFlow:
    """Integration tests for signup and unregister flows."""
    
    def test_signup_then_unregister(self, client, reset_activities):
        """Test signing up and then unregistering."""
        email = "tempstudent@mergington.edu"
        activity = "Science Club"
        
        # Sign up
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert response.status_code == 200
        
        # Verify in list
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]
        
        # Unregister
        response = client.delete(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert response.status_code == 200
        
        # Verify removed
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]
    
    def test_signup_again_after_unregister(self, client, reset_activities):
        """Test that you can sign up again after unregistering."""
        email = "tempstudent@mergington.edu"
        activity = "Science Club"
        
        # Sign up
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert response.status_code == 200
        
        # Unregister
        client.delete(
            f"/activities/{activity}/unregister?email={email}"
        )
        
        # Sign up again
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert response.status_code == 200
    
    def test_multiple_participants(self, client, reset_activities):
        """Test multiple participants in the same activity."""
        activity = "Art Studio"
        emails = [
            "student1@mergington.edu",
            "student2@mergington.edu",
            "student3@mergington.edu"
        ]
        
        # Sign up multiple students
        for email in emails:
            response = client.post(
                f"/activities/{activity}/signup?email={email}"
            )
            assert response.status_code == 200
        
        # Verify all are registered
        response = client.get("/activities")
        participants = response.json()[activity]["participants"]
        for email in emails:
            assert email in participants
        
        # Unregister one
        response = client.delete(
            f"/activities/{activity}/unregister?email=student2@mergington.edu"
        )
        assert response.status_code == 200
        
        # Verify the others remain
        response = client.get("/activities")
        participants = response.json()[activity]["participants"]
        assert "student1@mergington.edu" in participants
        assert "student2@mergington.edu" not in participants
        assert "student3@mergington.edu" in participants

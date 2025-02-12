import pytest
from flask import session
from src.models import User

def test_register(client):
    """Test registration."""
    response = client.post('/auth/register', json={
        'username': 'test',
        'password': 'test123',
        'email': 'test@example.com'
    })
    assert response.status_code == 200
    assert response.json['success'] is True

def test_login(client, test_user):
    """Test login."""
    response = client.post('/auth/login', json={
        'username': 'test',
        'password': 'test'
    })
    assert response.status_code == 200
    assert response.json['success'] is True

def test_logout(client, auth, test_user):
    """Test logout."""
    # First login
    auth.login()
    
    # Then logout
    response = auth.logout()
    assert response.status_code == 302  # Redirect to login page

def test_invalid_login(client):
    """Test login with invalid credentials."""
    response = client.post('/auth/login', json={
        'username': 'nonexistent',
        'password': 'wrong'
    })
    assert response.status_code == 401
    assert response.json['success'] is False

def test_register_existing_user(client, test_user):
    """Test registration with existing username."""
    response = client.post('/auth/register', json={
        'username': 'test',
        'password': 'test123',
        'email': 'another@example.com'
    })
    assert response.status_code == 400
    assert response.json['success'] is False

def test_protected_route(client):
    """Test accessing protected route without authentication."""
    response = client.get('/dashboard')
    assert response.status_code == 302  # Redirect to login

def test_password_validation(client):
    """Test password validation during registration."""
    # Test short password
    response = client.post('/auth/register', json={
        'username': 'newuser',
        'password': 'short',
        'email': 'new@example.com'
    })
    assert response.status_code == 400
    assert response.json['success'] is False

def test_email_validation(client):
    """Test email validation during registration."""
    # Test invalid email
    response = client.post('/auth/register', json={
        'username': 'newuser',
        'password': 'test123',
        'email': 'invalid-email'
    })
    assert response.status_code == 400
    assert response.json['success'] is False 
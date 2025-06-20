def test_register_new_user(client):
    """Test that a new user can register and is redirected to the login page."""
    response = client.post("/register", data={"username": "newuser", "password": "newpass"}, follow_redirects=False)
    assert response.status_code in (302, 303)
    assert response.headers["location"] == "/login"


def test_register_duplicate_user(client):
    """Ensure registering with a duplicate username returns a 400 error and relevant message."""
    client.post("/register", data={"username": "dupeuser", "password": "first"})
    response = client.post("/register", data={"username": "dupeuser", "password": "second"})
    assert response.status_code == 400
    assert "Username already registered" in response.text


def test_login_valid_credentials(client):
    """Test that a user can log in with valid credentials and receives an access token cookie."""
    client.post("/register", data={"username": "logme", "password": "secure"})
    response = client.post("/login", data={"username": "logme", "password": "secure"}, follow_redirects=False)
    assert response.status_code == 302
    assert "access_token=" in response.headers["set-cookie"]


def test_login_invalid_credentials(client):
    """Verify that logging in with incorrect credentials returns a 401 Unauthorized status."""
    response = client.post("/login", data={"username": "ghost", "password": "wrong"})
    assert response.status_code == 401


def test_logout_clears_cookie(client):
    """Confirm that logging out clears the access token by setting an expired cookie."""
    client.post("/register", data={"username": "byeuser", "password": "bye"})
    client.post("/login", data={"username": "byeuser", "password": "bye"})
    response = client.get("/logout", follow_redirects=False)
    assert response.status_code == 302
    set_cookie = response.headers.get("set-cookie", "")
    assert "access_token=" in set_cookie
    assert 'Max-Age=0' in set_cookie or 'expires=' in set_cookie
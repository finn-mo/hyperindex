def test_register_new_user(client):
    response = client.post("/register", data={"username": "newuser", "password": "newpass"})
    assert response.status_code == 200
    assert response.json()["status"] == "registered"


def test_register_duplicate_user(client):
    client.post("/register", data={"username": "dupeuser", "password": "first"})
    response = client.post("/register", data={"username": "dupeuser", "password": "second"})
    assert response.status_code == 400
    assert "Username already registered" in response.text


def test_login_valid_credentials(client):
    client.post("/register", data={"username": "logme", "password": "secure"})
    response = client.post("/login", data={"username": "logme", "password": "secure"}, follow_redirects=False)
    assert response.status_code == 302
    assert "access_token=" in response.headers["set-cookie"]


def test_login_invalid_credentials(client):
    response = client.post("/login", data={"username": "ghost", "password": "wrong"})
    assert response.status_code == 401


def test_logout_clears_cookie(client):
    client.post("/register", data={"username": "byeuser", "password": "bye"})
    client.post("/login", data={"username": "byeuser", "password": "bye"})
    response = client.get("/logout", follow_redirects=False)
    assert response.status_code == 302
    set_cookie = response.headers.get("set-cookie", "")
    assert "access_token=" in set_cookie
    assert 'Max-Age=0' in set_cookie or 'expires=' in set_cookie

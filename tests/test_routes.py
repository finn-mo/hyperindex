def test_yellowpages_public_view(client):
    """Ensure the yellowpages root URL renders successfully for anonymous users."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "<title>" in response.text  # basic sanity check for HTML content


def test_rolodex_requires_login(client):
    """Ensure /rolodex is protected and returns 401 when not authenticated."""
    response = client.get("/rolodex")
    assert response.status_code == 401

def test_rolodex_authenticated_access(client, access_token):
    """Ensure authenticated users can access their personal rolodex."""
    response = client.get("/rolodex", cookies={"access_token": access_token})
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
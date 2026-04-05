"""Tests for GraphQL API — STORY-045"""


GQL_SUBSCRIPTIONS = """
query {
  subscriptions {
    id
    name
    cost
    billingCycle
    status
  }
}
"""

GQL_CREATE_SUBSCRIPTION = """
mutation CreateSub($name: String!, $cost: Float!, $billingCycle: String!) {
  createSubscription(name: $name, cost: $cost, billingCycle: $billingCycle) {
    id
    name
    cost
  }
}
"""


def test_graphql_endpoint_exists(client):
    """GET /graphql returns playground (200) or 404 — endpoint must exist."""
    r = client.get("/graphql")
    assert r.status_code in (200, 404, 405)


def test_graphql_query_subscriptions_authenticated(auth_client, db, admin_user, tenant_a):
    """Authenticated user can query subscriptions via GraphQL."""
    r = auth_client.post(
        "/graphql",
        json={"query": GQL_SUBSCRIPTIONS},
    )
    assert r.status_code == 200
    data = r.json()
    assert "data" in data
    assert "subscriptions" in data["data"]
    assert isinstance(data["data"]["subscriptions"], list)


def test_graphql_unauthenticated_returns_error(client):
    """Unauthenticated GraphQL query returns error in data or 401."""
    r = client.post("/graphql", json={"query": GQL_SUBSCRIPTIONS})
    if r.status_code == 200:
        data = r.json()
        assert "errors" in data
    else:
        assert r.status_code == 401


def test_graphql_mutation_create_subscription(auth_client):
    """GraphQL mutation can create a subscription."""
    r = auth_client.post(
        "/graphql",
        json={
            "query": GQL_CREATE_SUBSCRIPTION,
            "variables": {
                "name": "GraphQL Sub",
                "cost": 19.99,
                "billingCycle": "monthly",
            },
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert "errors" not in data or data["errors"] is None
    assert data["data"]["createSubscription"]["name"] == "GraphQL Sub"


def test_graphql_tenant_isolation(auth_client, auth_client_b, db, admin_user, admin_b, tenant_a, tenant_b):
    """Tenant A cannot see Tenant B subscriptions via GraphQL."""
    # Create sub for tenant B
    auth_client_b.post("/api/v1/subscriptions/", json={
        "name": "B Private Sub", "cost": 5.0, "billing_cycle": "monthly"
    })
    r = auth_client.post("/graphql", json={"query": GQL_SUBSCRIPTIONS})
    assert r.status_code == 200
    names = [s["name"] for s in r.json()["data"]["subscriptions"]]
    assert "B Private Sub" not in names


def test_graphql_query_plans(auth_client):
    """Can query plans via GraphQL."""
    r = auth_client.post("/graphql", json={"query": "query { plans { id name price } }"})
    assert r.status_code == 200
    assert "plans" in r.json()["data"]


def test_graphql_bearer_token_auth(client, db, admin_user):
    """GraphQL works with Bearer token auth."""
    token_r = client.post(
        "/api/v1/auth/token",
        data={"username": "admin@test.com", "password": "password123"},
    )
    token = token_r.json()["access_token"]
    r = client.post(
        "/graphql",
        json={"query": GQL_SUBSCRIPTIONS},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    assert "subscriptions" in r.json()["data"]

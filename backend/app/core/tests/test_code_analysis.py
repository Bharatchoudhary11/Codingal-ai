from __future__ import annotations

import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_analyze_code_flags_unused_variable(client):
    code = """
value = 3
print('hello world')
"""
    response = client.post(reverse("analyze-code"), data={"code": code}, format="json")
    assert response.status_code == 200
    rules = {issue["rule"] for issue in response.json()["issues"]}
    assert "unused-variable" in rules


@pytest.mark.django_db
def test_analyze_code_detects_off_by_one_range(client):
    code = """
def iterate(values):
    for index in range(len(values) + 1):
        print(values[index])
"""
    response = client.post(reverse("analyze-code"), data={"code": code}, format="json")
    assert response.status_code == 200
    rules = {issue["rule"] for issue in response.json()["issues"]}
    assert "for-loop-off-by-one" in rules


@pytest.mark.django_db
def test_analyze_code_warns_on_missing_return(client):
    code = """
def compute_total(numbers):
    total = 0
    for number in numbers:
        total += number
"""
    response = client.post(reverse("analyze-code"), data={"code": code}, format="json")
    assert response.status_code == 200
    rules = {issue["rule"] for issue in response.json()["issues"]}
    assert "missing-return" in rules


@pytest.mark.django_db
def test_analyze_code_spots_duplicate_blocks(client):
    code = """
def describe(flag):
    if flag:
        print('duplicate')
    else:
        print('duplicate')
"""
    response = client.post(reverse("analyze-code"), data={"code": code}, format="json")
    assert response.status_code == 200
    payload = response.json()
    assert any(issue["rule"] == "duplicate-block" for issue in payload["issues"])


@pytest.mark.django_db
def test_analyze_code_accepts_clean_snippet(client):
    code = """
from statistics import mean

def summarise(values):
    if not values:
        return 0
    return mean(values)
"""
    response = client.post(reverse("analyze-code"), data={"code": code}, format="json")
    assert response.status_code == 200
    assert response.json()["issues"] == []

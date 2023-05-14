from tests.conftest import client



def test_post_couriers():
    couriers_data = [
        {"courier_type": "BIKE", "regions": [1, 2, 3], "working_hours": "16:00-20:00"},
        {"courier_type": "AUTO", "regions": [1, 2], "working_hours": "09:00-18:00"}
    ]

    response = client.post("/couriers", json=couriers_data)

    assert response.status_code == 200
    assert response.json() == couriers_data


def test_get_assignments_couriers():
    response = client.get("/couriers/assignments")

    assert response.status_code == 200



def test_get_courier_info():
    courier_id = 1

    response = client.get(f"/couriers/{courier_id}")

    assert response.status_code == 200



def test_get_all_couriers_info():
    response = client.get("/couriers?offset=0&limit=1")

    assert response.status_code == 200



def test_get_meta_couriers_info():
    courier_id = 1
    start_date = "2023-01-01"
    end_date = "2023-12-31"

    response = client.get(f"/couriers/meta-info/{courier_id}?start_date={start_date}&end_date={end_date}")

    assert response.status_code == 200


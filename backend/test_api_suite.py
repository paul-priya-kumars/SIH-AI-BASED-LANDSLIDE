import requests
import io

BASE = 'http://127.0.0.1:8000'

def run_tests():
    print("Running Full-Stack Backend Integration Tests...")

    # 1. Health
    r = requests.get(f'{BASE}/api/health')
    assert r.status_code == 200, f'Health failed: {r.text}'
    print('[PASS] [GET /api/health] Status OK')

    # 2. Risk
    r = requests.get(f'{BASE}/api/risk?latitude=11.4102&longitude=76.6950')
    assert r.status_code == 200, f'Risk failed: {r.text}'
    data = r.json()
    assert data['risk_level'] == 'VERY_HIGH'
    print(f"[PASS] [GET /api/risk] Prediction: {data['risk_level']} ({data['risk_probability']*100:.0f}%), Factors: {len(data['factors'])}")

    # 3. Environment
    r = requests.get(f'{BASE}/api/environment?latitude=11.4102&longitude=76.6950')
    assert r.status_code == 200, f'Environment failed: {r.text}'
    env = r.json()
    assert env['rainfall'] == 145.0
    print(f"[PASS] [GET /api/environment] Rainfall: {env['rainfall']}mm, Slope: {env['slope']} deg, Elev: {env['elevation']}m, NDVI: {env['ndvi']}")

    # 4. Risk Zones
    r = requests.get(f'{BASE}/api/risk-zones')
    assert r.status_code == 200, f'Zones failed: {r.text}'
    zones = r.json()
    assert len(zones) >= 6
    print(f"[PASS] [GET /api/risk-zones] Retrieved {len(zones)} GIS hazard zones")

    # 5. Route Risk
    r = requests.get(f'{BASE}/api/route-risk?start=Coonoor&destination=Ooty')
    assert r.status_code == 200, f'Route failed: {r.text}'
    route = r.json()
    assert 'recommended_route' in route
    print(f"[PASS] [GET /api/route-risk] Evaluated: {route['recommended_route']['name']} vs {route['alternative_route']['name']}")

    # 6. Alerts
    r = requests.get(f'{BASE}/api/alerts')
    assert r.status_code == 200, f'Alerts failed: {r.text}'
    alerts = r.json()
    assert len(alerts) >= 5
    print(f"[PASS] [GET /api/alerts] Retrieved {len(alerts)} active warning bulletins")

    # 7. Submit Citizen Hazard Report with Photograph
    img_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    files = {'image': ('hazard_photo.png', io.BytesIO(img_bytes), 'image/png')}
    form_data = {
        'latitude': 11.3920,
        'longitude': 76.7510,
        'hazard_type': 'Rockfall',
        'description': 'Massive boulder fracture tumbling across outer shoulder of hairpin 8. Road partially blocked.',
        'severity': 'CRITICAL',
        'location_name': 'Coonoor Hairpin 8',
        'contact_name': 'Ramesh Sharma',
        'contact_phone': '+91 98410 99887'
    }
    r = requests.post(f'{BASE}/api/reports', data=form_data, files=files)
    assert r.status_code == 200, f'Report creation failed: {r.text}'
    rep = r.json()
    report_id = rep['report_id']
    print(f"[PASS] [POST /api/reports] Submitted report #{report_id} with photo URL: {rep['image_url']}")

    # 8. Retrieve report
    r = requests.get(f'{BASE}/api/reports/{report_id}')
    assert r.status_code == 200, f'Get report failed: {r.text}'
    print(f"[PASS] [GET /api/reports/{{id}}] Successfully fetched report #{report_id}")

    # 9. Update Status (Authority workflow)
    r = requests.patch(f'{BASE}/api/reports/{report_id}/status', json={'status': 'VERIFIED'})
    assert r.status_code == 200, f'Status update failed: {r.text}'
    updated = r.json()
    assert updated['status'] == 'VERIFIED'
    print(f"[PASS] [PATCH /api/reports/{{id}}/status] Report status successfully transitioned to: {updated['status']}")

    # 10. M1 Contract Endpoint
    ml_payload = {
        'latitude': 11.41,
        'longitude': 76.69,
        'features': {
            'rainfall': 145.0,
            'slope': 37.0,
            'elevation': 2240.0,
            'ndvi': 0.43
        }
    }
    r = requests.post(f'{BASE}/api/ml/predict', json=ml_payload)
    assert r.status_code == 200, f'ML predict failed: {r.text}'
    ml_resp = r.json()
    print(f"[PASS] [POST /api/ml/predict] M1 contract response: {ml_resp['risk_level']} (Prob: {ml_resp['risk_probability']})")

    print("\nALL 10 API INTEGRATION TESTS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    run_tests()

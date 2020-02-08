import json
from . import app, client, create_token, db_reset, cache

class TestUsers():
    # Show users profile
    def test_users_profile(self, client):
        # Prepare the DB and token
        db_reset()
        token = create_token('hedy@alterra.id')

        # Test the endpoints
        res = client.get('/user/profile', headers={'Authorization': 'Bearer ' + token})
        res_json = json.loads(res.data)
        assert res.status_code == 200
    
    def test_valid_edit_profile(self, client):
        # Prepare the DB and token
        db_reset()
        token = create_token('hedy@alterra.id')

        # Prepare the data to be inputted
        data = {
            "fullname": "Hedy Gading",
            "password": "Gading09",
            "phone_number": "089511447629",
            "business_name": "Mie-Niac",
            "image": "https://dummy.jpg"
        }

        # Test the endpoints
        res = client.put('/user/profile', json = data, headers={'Authorization': 'Bearer ' + token})
        res_json = json.loads(res.data)
        assert res.status_code == 200
    
    def test_edit_profile_not_match_password(self, client):
        # Prepare the DB and token
        db_reset()
        token = create_token('hedy@alterra.id')

        # Prepare the data to be inputted
        data = {
            "fullname": "Hedy Gading",
            "password": "justgading",
            "phone_number": "089511447629",
            "business_name": "Mie-Niac",
            "image": "https://dummy.jpg"
        }

        # Test the endpoints
        res = client.put('/user/profile', json = data, headers={'Authorization': 'Bearer ' + token})
        res_json = json.loads(res.data)
        assert res.status_code == 422
        
    def test_edit_profile_empty_field(self, client):
        # Prepare the DB and token
        db_reset()
        token = create_token('hedy@alterra.id')

        # Prepare the data to be inputted
        data = {
            "fullname": "",
            "password": "Gading09",
            "phone_number": "089511447629",
            "business_name": "Mie-Niac",
            "image": "https://dummy.jpg"
        }

        # Test the endpoints
        res = client.put('/user/profile', json = data, headers={'Authorization': 'Bearer ' + token})
        res_json = json.loads(res.data)
        assert res.status_code == 400
        assert res_json['message'] == 'Tidak boleh ada kolom yang dikosongkan'
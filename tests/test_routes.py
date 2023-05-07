"""
Account API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import os
import logging
from unittest import TestCase
from tests.factories import AccountFactory
from service.common import status  # HTTP Status Codes
from service.models import db, Account, init_db
from service.routes import app
from datetime import date
from service import talisman

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL = "/accounts"

HTTPS_ENVIRON = {'wsgi.url_scheme': 'https'}


######################################################################
#  T E S T   C A S E S
######################################################################
class TestAccountService(TestCase):
    """Account Service Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)
        talisman.force_https = False

    @classmethod
    def tearDownClass(cls):
        """Runs once before test suite"""

    def setUp(self):
        """Runs before each test"""
        db.session.query(Account).delete()  # clean up the last tests
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """Runs once after each test case"""
        db.session.remove()

    ######################################################################
    #  H E L P E R   M E T H O D S
    ######################################################################

    def _create_accounts(self, count):
        """Factory method to create accounts in bulk"""
        accounts = []
        for _ in range(count):
            account = AccountFactory()
            response = self.client.post(BASE_URL, json=account.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test Account",
            )
            new_account = response.get_json()
            account.id = new_account["id"]
            accounts.append(account)
        return accounts

    ######################################################################
    #  A C C O U N T   T E S T   C A S E S
    ######################################################################

    def test_index(self):
        """It should get 200_OK from the Home Page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health(self):
        """It should be healthy"""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "OK")

    def test_create_account(self):
        """It should Create a new Account"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_account = response.get_json()
        self.assertEqual(new_account["name"], account.name)
        self.assertEqual(new_account["email"], account.email)
        self.assertEqual(new_account["address"], account.address)
        self.assertEqual(new_account["phone_number"], account.phone_number)
        self.assertEqual(new_account["date_joined"], str(account.date_joined))

    def test_bad_request(self):
        """It should not Create an Account when sending the wrong data"""
        response = self.client.post(BASE_URL, json={"name": "not enough data"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        """It should not Create an Account when sending the wrong media type"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="test/html"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    # ADD YOUR TEST CASES HERE ...
    def test_list_all_accounts(self):
        """ It should be able to list all accounts """
        # Given three accounts in the service with ids 1, 2 and 3
        created_accounts = self._create_accounts(3)
        generated_ids = {account.id for account in created_accounts}

        # When I view the interface for all accounts
        response = self.client.get("/accounts")
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        response_accounts = [account for account in response.get_json()]
        response_ids = {account["id"] for account in response_accounts}

        # Then I should be able to see all three accounts with ids 1, 2, and 3 in the service
        self.assertEqual(len(created_accounts), len(response_accounts))
        self.assertSetEqual(generated_ids, response_ids)
        
    def test_read_account(self):
        """ It should be able to read an account"""
        # Given three accounts in the service with ids 1, 2 and 3
        created_accounts = self._create_accounts(3)
        account_to_view = created_accounts[1]

        # When I read the account with id 2
        response = self.client.get(f"/accounts/{account_to_view.id}")
        response_account = response.get_json()

        # Then I should be able to see all information of the account with id 2
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(response_account["id"], account_to_view.id)
        self.assertEqual(response_account["name"], account_to_view.name)
        self.assertEqual(response_account["email"], account_to_view.email)
        self.assertEqual(response_account["address"], account_to_view.address)
        self.assertEqual(response_account["phone_number"], account_to_view.phone_number)
        self.assertEqual(response_account["date_joined"], account_to_view.date_joined.strftime("%Y-%m-%d"))
    
    def test_read_account_does_not_exist(self):
        """ It shouldn't read an account that doesn't exist """
        response = self.client.get("/accounts/1")
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)
    
    def test_read_invalid_account_id(self):
        """ It should validate that the id to read is valid """
        response = self.client.get("/accounts/sample")
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_update_account(self):
        """ It should be able to update an account """
        # Given an account
        created_account = AccountFactory()
        create_response = self.client.post("/accounts", json=created_account.serialize())
        self.assertEqual(status.HTTP_201_CREATED, create_response.status_code)
        created_account = create_response.get_json()
        original_account = created_account.copy()

        # When I update the information of the account with new and different information
        created_account["name"] = "Other Name"
        created_account["email"] = "other@email.com"
        created_account["address"] = "other address"
        created_account["phone_number"] = "0911111"
        created_account["date_joined"] = "1999-01-01"
        update_response = self.client.put(f"/accounts/{created_account['id']}", json=created_account)
        self.assertEqual(status.HTTP_200_OK, update_response.status_code)
        updated_account = update_response.get_json()

        # Then the information must have changed when I view the account again 
        self.assertNotEqual(original_account["name"], updated_account["name"])
        self.assertNotEqual(original_account["email"], updated_account["email"])
        self.assertNotEqual(original_account["address"], updated_account["address"])
        self.assertNotEqual(original_account["phone_number"], updated_account["phone_number"])
        self.assertNotEqual(original_account["date_joined"], updated_account["date_joined"])

        # and the information on the account must be equal to the new information I set it
        self.assertEqual(created_account["name"], updated_account["name"])
        self.assertEqual(created_account["email"], updated_account["email"])
        self.assertEqual(created_account["address"], updated_account["address"])
        self.assertEqual(created_account["phone_number"], updated_account["phone_number"])
        self.assertEqual(created_account["date_joined"], updated_account["date_joined"])

    def test_update_account_does_not_exist(self):
        """ It shouldn't update an account that doesn't exist """
        response = self.client.put(f"/accounts/1")
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)
    
    def test_update_invalid_account_id(self):
        """ It should validate that the id to update is valid """
        response = self.client.put(f"/accounts/sample")
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_delete_account(self):
        """ It should be able to delete an account"""
        # Given an account from the service
        created_account = AccountFactory()
        create_response = self.client.post("/accounts", json=created_account.serialize())
        self.assertEqual(status.HTTP_201_CREATED, create_response.status_code)
        created_account = create_response.get_json()

        # When I delete the account
        delete_response = self.client.delete(f"/accounts/{created_account['id']}")
        self.assertEqual(status.HTTP_204_NO_CONTENT, delete_response.status_code)
        
        # Then I shouldn't be able to view and interact with the account anymore
        # Cannot View
        view_response = self.client.get(f"/accounts/{created_account['id']}")
        self.assertEqual(status.HTTP_404_NOT_FOUND, view_response.status_code)

        # Cannot update
        update_response = self.client.put(f"/accounts/{created_account['id']}")
        self.assertEqual(status.HTTP_404_NOT_FOUND, update_response.status_code)

        # Cannot delete
        delete_response = self.client.delete(f"/accounts/{created_account['id']}")
        self.assertEqual(status.HTTP_404_NOT_FOUND, delete_response.status_code)

    def test_delete_account_does_not_exist(self):
        """ It shouldn't delete an account that doesn't exist """
        response = self.client.delete("/accounts/1")
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)
    
    def test_delete_invalid_account_id(self):
        """ It should validate that the id to delete is valid """
        response = self.client.delete("/accounts/sample")
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_method_not_allowed(self):
        self._create_accounts(3)

        # DELETE /account is not allowed
        response = self.client.delete(f"/accounts")
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, response.status_code)

        # PUT /account is not allowed
        response = self.client.put(f"/accounts")
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, response.status_code)

    def test_secure_headers(self):
        """ It should have secure headers """
        response = self.client.get("/?environ_overrides=HTTPS_ENVIRON")
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        expected_headers = {
            'X-Frame-Options': 'SAMEORIGIN',
            'X-XSS-Protection': '1; mode=block',
            'X-Content-Type-Options': 'nosniff',
            'Content-Security-Policy': 'default-src \'self\'; object-src \'none\'',
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
        self.assertDictContainsSubset(expected_headers, response.headers)
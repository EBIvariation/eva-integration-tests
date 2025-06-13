import os
import re

import requests


class WebinTestUser:
    webin_test_user_url = "https://wwwdev.ebi.ac.uk/ena/submit/webin/auth/admin/submission-account"

    def __init__(self, email=None, password=None):
        print("Env check:", os.getenv("WEBIN_TEST_USER_EMAIL"))
        print("Env check:", os.getenv("WEBIN_TEST_USER_PASSWORD"))
        self.webin_test_user_email = email or os.getenv("WEBIN_TEST_USER_EMAIL")
        self.webin_test_user_password = password or os.getenv("WEBIN_TEST_USER_PASSWORD")
        self.webin_test_user_account_id = None

    def create_webin_test_user(self):
        user_details = {
            "submissionAccountId": "",
            "centerName": "test-center",
            "fullCenterName": "test-center",
            "brokerName": "test-broker",
            "laboratoryName": "test-laboratory",
            "country": "United Kingdom",
            "address": "Welcome Genome Campus",
            "metagenomeSubmitter": False,
            "metagenomicsAnalysis": False,
            "suspended": "N",
            "webinPassword": self.webin_test_user_password,
            "submissionContacts": [
                {
                    "consortium": "",
                    "emailAddress": self.webin_test_user_email,
                    "firstName": "eva-sub-cli",
                    "mainContact": True,
                    "middleInitials": "",
                    "submissionAccountId": "",
                    "surname": "test"
                }
            ]
        }

        response = requests.post(self.webin_test_user_url, json=user_details)
        if response.status_code == 201:
            self.webin_test_user_account_id = response.json()['submissionAccountId']
        elif response.status_code == 400 and f"already exists with {self.webin_test_user_email} as the main contact" in response.text:
            match = re.search(r"Webin-\d+", response.text)
            self.webin_test_user_account_id = match.group().strip()
        else:
            raise Exception("Could not register user in Webin. Error: " + response.text)

    def get_webin_submission_account_id_and_password(self):
        if not self.webin_test_user_account_id:
            self.create_webin_test_user()

        return self.webin_test_user_account_id, self.webin_test_user_password

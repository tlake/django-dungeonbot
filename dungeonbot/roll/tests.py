from rest_framework.reverse import reverse
from rest_framework import status
from rest_framework.test import APITestCase

import json


class RollAPITests(APITestCase):
    def test_blank_roll_endpoint(self):
        """
        Ensure `GET /roll/` returns a sample roll to make.
        """
        url = reverse("roll-list")
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("sample_roll", response.data.keys())

    def test_valid_inputs(self):
        """
        Ensure that various inputs which are supposed to be valid
        are actually valid.
        """
        valid_inputs = [
            "2d4",
            "2d4+2",
            "2d4+2d4",
            "2d4+2+2d4",
            "(2d4)",
            "2*2d4",
            "2d4*2",
            "2d4,2d4",
            ",",
            "3*(2d4+2),(2d4-2)|2",
            "1",
            "400d2",
            "2d400",
        ]

        for i in valid_inputs:
            url = reverse("roll-detail", args=[i])
            response = self.client.get(url, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_inputs(self):
        """
        Ensure that bad inputs resolve with appropriate responses.
        """
        invalid_inputs = [
            "string",
            "string with spaces",
            "2d",
            # "2d2d2", TODO: Figure out why this randomly succeeds or fails
            "3(2d4)",
            "d",
        ]

        for i in invalid_inputs:
            url = reverse("roll-detail", args=[i])
            response = self.client.get(url, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class SavedRollAPITests(APITestCase):
    def test_idempotent_post(self):
        """
        Ensure POST updates if there's a match instead of creating a duplicate.
        """
        url = reverse("saved_roll-list")
        data = {
            "group": "test group",
            "user": "test user",
            "name": "test name",
            "content": "test content",
        }

        state_0 = len(json.loads(self.client.get(url).content))
        resp_0 = self.client.post(url, data)

        data["content"] = "test content 2"
        state_1 = len(json.loads(self.client.get(url).content))
        resp_1 = self.client.post(url, data)

        state_2 = len(json.loads(self.client.get(url).content))

        self.assertGreater(state_1, state_0)
        self.assertEqual(state_1, state_2)
        self.assertEqual(json.loads(resp_0.content)["content"], "test content")
        self.assertEqual(json.loads(resp_1.content)["content"], "test content 2")

    def test_post_bad_data(self):
        url = reverse("saved_roll-list")
        data = {
            "group": 1234,
            "user": "",
            "name": "",
            "content": "",
        }

        resp = self.client.post(url, data)

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_too_many_characters(self):
        """
        Confirm failure with strings that are too long.
        """
        url = reverse("saved_roll-list")
        too_long = "q" * 300
        data = {
            "group": too_long,
            "user": "test user",
            "name": "test name",
            "content": "test content",
        }

        resp = self.client.post(url, data)

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_calc_simple_saved_roll(self):
        """
        Confirm that a saved roll can be calculated.
        """
        data = {
            "group": "test group",
            "user": "test user",
            "name": "test name",
            "content": "2d4",
        }

        post_resp = self.client.post(reverse("saved_roll-list"), data)
        saved_roll = post_resp.data

        url = reverse("saved_roll-calc", args=[saved_roll["id"]])
        resp = self.client.get(url)

        self.assertIsInstance(json.loads(resp.content)[0], int)

    def test_calc_with_bad_saved_roll_string(self):
        """
        Confirm that calc returns the proper error if the saved roll is bad.
        """
        data = {
            "group": "test group",
            "user": "test user",
            "name": "test name",
            "content": "2d",
        }

        post_resp = self.client.post(reverse("saved_roll-list"), data)
        saved_roll = post_resp.data

        url = reverse("saved_roll-calc", args=[saved_roll["id"]])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 400)

    def test_calc_with_multipart_roll(self):
        """
        Confirm that calc can handle multipart roll strings.
        """
        data = {
            "group": "test group",
            "user": "test user",
            "name": "test name",
            "content": "3*(2d4+4d2)+2",
        }

        post_resp = self.client.post(reverse("saved_roll-list"), data)
        saved_roll = post_resp.data

        url = reverse("saved_roll-calc", args=[saved_roll["id"]])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(json.loads(resp.content)[0], int)

    def test_calc_with_multiple_rolls(self):
        """
        Confirm that calc can handle multiple rolls contained in one saved roll.
        """
        data = {
            "group": "test group",
            "user": "test user",
            "name": "test name",
            "content": "2d4,2d4,2d4",
        }

        post_resp = self.client.post(reverse("saved_roll-list"), data)
        saved_roll = post_resp.data

        url = reverse("saved_roll-calc", args=[saved_roll["id"]])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(json.loads(resp.content)[0], int)
        self.assertEqual(len(json.loads(resp.content)), 3)

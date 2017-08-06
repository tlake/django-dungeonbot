from rest_framework.reverse import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class RollTests(APITestCase):
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
            "butts",
            "2d",
            # "2d2d2", TODO: Figure out why this randomly succeeds or fails
            "3(2d4)",
            "d",
        ]

        for i in invalid_inputs:
            url = reverse("roll-detail", args=[i])
            response = self.client.get(url, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework.reverse import reverse

import json
from random import randint


class DieRollerViewSet(ViewSet):
    """
    ## GET
    **Makes any number of comma-separated die rolls.**

    Write these rolls as if they could be evaluated mathematically by Python.

    Examples:

    - `/roll/1d20/`
    - `/roll/2d4+2,4d4+4/`
    - `/roll/3*(2d12-4)/`
    """

    def list(self, request):
        return Response({"sample_roll": reverse("roll-detail", args=['2d4+2'], request=request)})

    def retrieve(self, request, pk):
        request_string = pk
        response = []

        allowed_chars = "1234567890d()*/+-,"
        if not self._string_is_safe(request_string, allowed_chars):
            msg = f"Only the following characters are allowed: {allowed_chars}"
            code = status.HTTP_400_BAD_REQUEST
            return Response(msg, code)

        roll_strings = request_string.split(",")

        for roll_string in roll_strings:
            processed_string = self._convert_dice_to_values(roll_string)
            try:
                evaluated_roll = eval(processed_string) if processed_string else None
            except SyntaxError:
                msg = f"Malformed die roll(s): {request_string}"
                code = status.HTTP_400_BAD_REQUEST
                return Response(msg, code)

            response.append(evaluated_roll)

        return Response(json.dumps(response))

    def _string_is_safe(self, string, whitelist):
        for char in string:
            if char not in whitelist:
                return False

        return True

    def _convert_dice_to_values(self, roll_string):
        # get the indices of all "d"s in the roll string;
        # these are the ocurrences of dice that need to be rolled
        replacements = []
        d_idxs = [i for i, v in enumerate(roll_string) if v == "d"]
        for d_idx in d_idxs:
            num_dice_idx, num_sides_idx = d_idx, d_idx

            while (
                roll_string[num_dice_idx - 1].isdigit()
                and num_dice_idx > 0
            ):
                num_dice_idx -= 1

            while (
                num_sides_idx < len(roll_string) - 2
                and roll_string[num_sides_idx + 2].isdigit()
            ):
                num_sides_idx += 1
            num_sides_idx += 2

            to_replace = roll_string[num_dice_idx:num_sides_idx]

            num_dice = int(roll_string[num_dice_idx:d_idx])
            num_sides = int(roll_string[d_idx+1:num_sides_idx])
            roll = sum([randint(1, num_sides) for n in range(num_dice)])

            replacements.append((to_replace, str(roll)))

        for source, value in replacements:
            roll_string = roll_string.replace(source, value, 1)

        return roll_string


class SavedRollViewSet(ViewSet):
    def get(self, request):
        return Response("Not yet implemented")

    def post(self, request):
        return Response("Not yet implemented")

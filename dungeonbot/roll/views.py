from rest_framework.viewsets import ViewSet, ModelViewSet
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from rest_framework import status
from rest_framework.reverse import reverse

from roll.models import SavedRoll
from roll.serializers import SavedRollSerializer

import json
from random import randint
import requests


class DieRollerViewSet(ViewSet):
    """
    ## GET
    **Makes any number of comma-separated die rolls.**

    Write these rolls as if they could be evaluated mathematically by Python.

    Examples:

    - `/roll/1d20/`
    - `/roll/2d4+2,4d4+4/`
    - `/roll/3*(2d12-4)/`

    Note: For division, use either the pipe character `|` or `%7C`.
    **Do not use `/`.**

    - `/roll/4d6|2/`
    - `/roll/4d6%7C2/`

    Also note that usage of division will return floats, not integers.
    """

    lookup_field = "rolls"

    def list(self, request):
        return Response({"sample_roll": reverse("roll-detail", args=['2d4+2'], request=request)})

    def retrieve(self, request, rolls):
        request_string = rolls
        response = []

        allowed_chars = "1234567890d()*|+-,"

        bad_input_msg = (
            f"Malformed die roll(s): {request_string}"
            f"\nNote: only the following characters are allowed: {allowed_chars}"
        )
        bad_input_response = Response(bad_input_msg, status.HTTP_400_BAD_REQUEST)

        if not self._string_is_safe(request_string, allowed_chars):
            return bad_input_response

        roll_strings = request_string.split(",")

        for roll_string in roll_strings:
            try:
                processed_string = self._convert_dice_to_values(roll_string)
            except ValueError:
                return bad_input_response

            try:
                evaluated_roll = eval(processed_string) if processed_string else None
            except (SyntaxError, TypeError):
                return bad_input_response

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

        return roll_string.replace("|", "/")


class SavedRollViewSet(ModelViewSet):
    """
    #### `/saved_roll/`
    - **GET**:
    List all saved rolls.

    - **POST**:
    Idempotent create-or-update operation.

    #### `/saved_roll/?{query}/`
    - **GET**:
    List all saved rolls that match the `{query}`.
    Available query params (may be joined with `&`):
        - `group=`
        - `user=`
        - `name=`

    #### `/saved_roll/{pk}/`
    - **GET**:
    Describe the saved roll with primary key `{pk}`.

    - **DELETE**:
    Delete the saved roll with primary key `{pk}`.

    #### `/saved_roll/{pk}/calc/`
    - **GET**:
    Calculate the saved roll with primary key `{pk}`.
    """

    queryset = SavedRoll.objects.all()
    serializer_class = SavedRollSerializer
    filter_fields = ["group", "user", "name"]

    def create(self, request):
        try:
            instance = SavedRoll.objects.get(
                group=request.data['group'],
                user=request.data['user'],
                name=request.data['name'],
            )
            serializer = SavedRollSerializer(instance=instance, data=request.data)
            if serializer.is_valid():
                saved_roll = serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            # not sure how to hit the following line:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)  # pragma: no cover
        except SavedRoll.DoesNotExist:
            serializer = SavedRollSerializer(data=request.data)
        if serializer.is_valid():
            saved_roll = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @detail_route(methods=['get'])
    def calc(self, request, pk):
        instance = SavedRoll.objects.get(id=pk)
        content = instance.content

        roller = DieRollerViewSet()
        resp = roller.retrieve(request, content)

        if resp.status_code != 200:
            return Response(resp.status_text, status=status.HTTP_400_BAD_REQUEST)

        return Response(json.loads(resp.data), status=status.HTTP_200_OK)

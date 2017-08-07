from rest_framework.serializers import ModelSerializer
from roll.models import SavedRoll


class SavedRollSerializer(ModelSerializer):
    class Meta:
        model = SavedRoll
        fields = ("id", "group", "user", "name", "content")

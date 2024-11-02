from rest_framework import serializers

from analysis.models import Category,Questionnaire,Options,Invoices,AnswerType

class CategorySerializer(serializers.ModelSerializer):
    image = serializers.ImageField(allow_null=True,required=False)
    class Meta:
        model = Category
        fields = "__all__"

class QuestionnaireSerializer(serializers.ModelSerializer):
    class Meta:
        model = Questionnaire
        fields="__all__"

class OptionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Options
        fields = "__all__"
        
class InvoicesSerializer(serializers.ModelSerializer):
    class Meta:
        model=Invoices
        fields="__all__"
class AnswerTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model=AnswerType
        fields="__all__"
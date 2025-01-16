from rest_framework import serializers
from .models import Session, Competency, Assessment, Profile


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = '__all__'


class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = '__all__'

    def validate_title(self, value):
        if not value:
            raise serializers.ValidationError(
                "Название сессии обязательно для заполнения.")
        return value

    def validate_evaluated(self, value):
        user_profile = Profile.objects.get(user=self.context['request'].user)
        if user_profile.role != 'hr_manager':
            raise serializers.ValidationError(
                "Только HR Manager может назначать сотрудника.")

        if not value:
            raise serializers.ValidationError(
                "Оцениваемый сотрудник обязателен для заполнения.")
        return value

    def validate_is_active(self, value):
        user_profile = Profile.objects.get(user=self.context['request'].user)
        if not value or user_profile.role != 'hr_manager':
            raise serializers.ValidationError(
                "Только HR Manager может активировать сессию.")
        return value


class CompetencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Competency
        fields = '__all__'

    def validate_name(self, value):
        if len(value) > 100:
            raise serializers.ValidationError(
                "Название компетенции не должно превышать 100 символов.")
        return value

    def validate_description(self, value):
        if value and len(value) > 300:
            raise serializers.ValidationError(
                "Описание компетенции не должно превышать 300 символов.")
        return value


class AssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assessment
        fields = '__all__'

    def validate_session(self, value):
        if not value:
            raise serializers.ValidationError(
                "Сессия обязательна для заполнения.")
        return value

    def validate_competency(self, value):
        if not value:
            raise serializers.ValidationError(
                "Компетенция обязательна для заполнения.")
        return value

    def validate_evaluator(self, value):
        if not value:
            raise serializers.ValidationError(
                "Оценщик обязателен для заполнения.")
        return value

    def validate_score(self, value):
        if value < 1 or value > 10:
            raise serializers.ValidationError(
                "Оценка должна быть в диапазоне от 1 до 10.")
        return value

    def validate_comment(self, value):
        if value and len(value) > 300:
            raise serializers.ValidationError(
                "Комментарий не должен превышать 300 символов.")
        return value

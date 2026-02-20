"""
Serializers for Kanban Board API.
"""
from django.contrib.auth.models import User

from rest_framework import serializers

from ..models import Board, Comment, Task


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User with profile data."""
    fullname = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'fullname']

    def get_fullname(self, obj):
        """Get fullname from profile."""
        return getattr(getattr(obj, 'profile', None), 'fullname', '')


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for Comment model."""
    author = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'created_at', 'author', 'content']
        read_only_fields = ['id', 'created_at', 'author']

    def get_author(self, obj):
        """Get author fullname."""
        profile = getattr(obj.author, 'profile', None)
        return profile.fullname if profile else obj.author.username


def get_board_member_ids(board):
    """Return list of member IDs including owner."""
    member_ids = list(board.members.values_list('id', flat=True))
    member_ids.append(board.owner_id)
    return member_ids


def get_board_for_validation(initial_data, instance):
    """Get board from data or instance."""
    board_id = initial_data.get('board') or (
        instance.board_id if instance else None)
    return Board.objects.filter(id=board_id).first() if board_id else None


class TaskSerializer(serializers.ModelSerializer):
    """Serializer for Task model."""
    assignee = UserSerializer(read_only=True)
    reviewer = UserSerializer(read_only=True)
    assignee_id = serializers.IntegerField(
        write_only=True, required=False, allow_null=True
    )
    reviewer_id = serializers.IntegerField(
        write_only=True, required=False, allow_null=True
    )
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'priority',
            'assignee', 'reviewer', 'assignee_id', 'reviewer_id',
            'due_date', 'board', 'comments_count'
        ]
        read_only_fields = ['id', 'assignee', 'reviewer', 'comments_count']

    def get_comments_count(self, obj):
        """Return the count of comments."""
        return obj.comments.count()

    def validate_assignee_id(self, value):
        """Validate assignee is board member."""
        if value is None:
            return value
        board = get_board_for_validation(self.initial_data, self.instance)
        if board and value not in get_board_member_ids(board):
            raise serializers.ValidationError("Assignee must be a member.")
        return value

    def validate_reviewer_id(self, value):
        """Validate reviewer is board member."""
        if value is None:
            return value
        board = get_board_for_validation(self.initial_data, self.instance)
        if board and value not in get_board_member_ids(board):
            raise serializers.ValidationError("Reviewer must be a member.")
        return value

    def create(self, validated_data):
        """Create task with assignee and reviewer."""
        assignee_id = validated_data.pop('assignee_id', None)
        reviewer_id = validated_data.pop('reviewer_id', None)
        if assignee_id:
            validated_data['assignee_id'] = assignee_id
        if reviewer_id:
            validated_data['reviewer_id'] = reviewer_id
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Update task with assignee and reviewer."""
        if 'assignee_id' in validated_data:
            instance.assignee_id = validated_data.pop('assignee_id')
        if 'reviewer_id' in validated_data:
            instance.reviewer_id = validated_data.pop('reviewer_id')
        return super().update(instance, validated_data)


class TaskListSerializer(serializers.ModelSerializer):
    """Serializer for Task list with board info."""
    assignee = UserSerializer(read_only=True)
    reviewer = UserSerializer(read_only=True)
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'id', 'board', 'title', 'description', 'status', 'priority',
            'assignee', 'reviewer', 'due_date', 'comments_count'
        ]

    def get_comments_count(self, obj):
        """Return the count of comments."""
        return obj.comments.count()


class BoardListSerializer(serializers.ModelSerializer):
    """Serializer for Board list view."""
    member_count = serializers.SerializerMethodField()
    ticket_count = serializers.SerializerMethodField()
    tasks_to_do_count = serializers.SerializerMethodField()
    tasks_high_prio_count = serializers.SerializerMethodField()
    owner_id = serializers.IntegerField(source='owner.id', read_only=True)

    class Meta:
        model = Board
        fields = [
            'id', 'title', 'member_count', 'ticket_count',
            'tasks_to_do_count', 'tasks_high_prio_count', 'owner_id'
        ]

    def get_member_count(self, obj):
        """Return count of members including owner."""
        if obj.members.filter(id=obj.owner_id).exists():
            return obj.members.count()
        return obj.members.count() + 1

    def get_ticket_count(self, obj):
        """Return total task count."""
        return obj.tasks.count()

    def get_tasks_to_do_count(self, obj):
        """Return count of to-do tasks."""
        return obj.tasks.filter(status='to-do').count()

    def get_tasks_high_prio_count(self, obj):
        """Return count of high priority tasks."""
        return obj.tasks.filter(priority='high').count()


class BoardDetailSerializer(serializers.ModelSerializer):
    """Serializer for Board detail view."""
    members = UserSerializer(many=True, read_only=True)
    tasks = TaskListSerializer(many=True, read_only=True)
    owner_id = serializers.IntegerField(source='owner.id', read_only=True)

    class Meta:
        model = Board
        fields = ['id', 'title', 'owner_id', 'members', 'tasks']


class BoardCreateSerializer(serializers.ModelSerializer):
    """Serializer for Board creation."""
    members = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True, required=False, default=[]
    )

    class Meta:
        model = Board
        fields = ['id', 'title', 'members']

    def create(self, validated_data):
        """Create board with members."""
        member_ids = validated_data.pop('members', [])
        board = Board.objects.create(**validated_data)
        if member_ids:
            board.members.set(User.objects.filter(id__in=member_ids))
        return board


class BoardUpdateSerializer(serializers.ModelSerializer):
    """Serializer for Board update."""
    members = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True, required=False
    )
    owner_data = UserSerializer(source='owner', read_only=True)
    members_data = UserSerializer(source='members', many=True, read_only=True)

    class Meta:
        model = Board
        fields = ['id', 'title', 'members', 'owner_data', 'members_data']

    def update(self, instance, validated_data):
        """Update board with members."""
        member_ids = validated_data.pop('members', None)
        instance.title = validated_data.get('title', instance.title)
        instance.save()
        if member_ids is not None:
            instance.members.set(User.objects.filter(id__in=member_ids))
        return instance 

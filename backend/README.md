# KanMind Backend

A Django REST Framework backend for a Kanban Board application.

## Setup

### 1. Clone the repository and navigate to the backend folder

```bash
git clone https://github.com/muc1982/KanMind1.0.git
cd KanMind1.0/backend
```

### 2. Create virtual environment

**Linux/Mac:**
```bash
python -m venv venv
source venv/bin/activate
```

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run migrations
```bash
python manage.py migrate
```

### 5. Create superuser (optional)
```bash
python manage.py createsuperuser
```

### 6. Run server
```bash
python manage.py runserver
```

## Running Tests

```bash
pytest
```

With coverage report:
```bash
pytest --cov=. --cov-report=html
```

## Project Structure

```
backend/
├── core/                   # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── auth_app/               # Authentication app
│   ├── models.py           # UserProfile model
│   └── api/
│       ├── serializers.py
│       ├── views.py
│       └── urls.py
├── kanban_app/             # Kanban board app
│   ├── models.py           # Board, Task, Comment models
│   ├── admin.py
│   └── api/
│       ├── serializers.py
│       ├── views.py
│       ├── urls.py
│       ├── permissions.py
│       └── utils.py
├── tests/                  # Test suite
│   ├── test_auth.py
│   ├── test_kanban.py
│   └── test_models.py
├── requirements.txt
├── pytest.ini
└── manage.py
```

## API Endpoints

### Authentication
- `POST /api/registration/` - Register new user
- `POST /api/login/` - Login and get token
- `GET /api/email-check/?email=` - Check if email exists (requires auth)

### Boards
- `GET /api/boards/` - List all boards
- `POST /api/boards/` - Create a new board
- `GET /api/boards/{id}/` - Get board details with tasks and members
- `PATCH /api/boards/{id}/` - Update board title and members
- `DELETE /api/boards/{id}/` - Delete board (owner only)

### Tasks
- `POST /api/tasks/` - Create a new task
- `PATCH /api/tasks/{id}/` - Update task
- `DELETE /api/tasks/{id}/` - Delete task (creator or board owner only)
- `GET /api/tasks/assigned-to-me/` - Get tasks assigned to current user
- `GET /api/tasks/reviewing/` - Get tasks where current user is reviewer

### Comments
- `GET /api/tasks/{task_id}/comments/` - List comments for a task
- `POST /api/tasks/{task_id}/comments/` - Create a comment
- `DELETE /api/tasks/{task_id}/comments/{id}/` - Delete a comment (author only)

## Authentication

Use Token Authentication. Include the token in the header:
```
Authorization: Token <your-token>
```

## Data Models

### User
- `id`: Integer
- `email`: String
- `fullname`: String (via UserProfile)

### Board
- `id`: Integer
- `title`: String
- `owner_id`: Integer
- `members`: Array of User objects

### Task
- `id`: Integer
- `title`: String
- `description`: String
- `status`: String (to-do, in-progress, review, done)
- `priority`: String (low, medium, high)
- `assignee`: User object or null
- `reviewer`: User object or null
- `due_date`: Date (YYYY-MM-DD) or null
- `board`: Integer
- `comments_count`: Integer

### Comment
- `id`: Integer
- `created_at`: ISO8601 Timestamp
- `author`: String (fullname)
- `content`: String

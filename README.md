# 📝 Prompt Templates - Django Web Application

A simple Django web application for storing and managing text templates/prompts.

## Features

- **Main Page (`main_paige.html`)**
  - Dropdown menu to select saved prompts
  - "NEW" button to create new prompts
  - Textarea to display selected prompt content
  - "Copy" button to copy content to clipboard

- **New Prompt Page (`new_prompt.html`)**
  - Textbox for prompt name
  - Textarea for prompt content
  - "Add" button to save the prompt
  - "Back" button to return to main page

## Project Structure

```
Prompt_WebSite/
├── manage.py                 # Django management script
├── requirements.txt          # Python dependencies
├── prompt_website/          # Django project settings
│   ├── __init__.py
│   ├── settings.py          # Project configuration
│   ├── urls.py              # URL routing
│   └── wsgi.py              # WSGI application
└── prompt_app/              # Django app for prompts
    ├── __init__.py
    ├── admin.py             # Admin configuration
    ├── apps.py              # App configuration
    ├── models.py            # Prompt model
    ├── views.py             # View functions
    ├── static/              # Static files
    └── templates/
        └── prompt_app/
            ├── main_paige.html    # Main page template
            └── new_prompt.html    # New prompt form template
```

## Setup Instructions

### 1. Install Dependencies

```bash
cd /home/adminsrv/Documents/Prompt_WebSite
pip install -r requirements.txt
```

### 2. Apply Database Migrations

```bash
python manage.py migrate
```

### 3. Create a Superuser (Optional)

```bash
python manage.py createsuperuser
```

### 4. Run the Development Server

```bash
python manage.py runserver 0.0.0.0:8000
```

### 5. Access the Application

Open your browser and navigate to:
- Main page: `http://localhost:8000/`
- New prompt: `http://localhost:8000/new_prompt/`
- Admin panel: `http://localhost:8000/admin/`

## Usage

### Main Page
1. Select a prompt from the dropdown menu to load its content
2. Click "NEW" to create a new prompt
3. Use the "Copy" button to copy the prompt content to clipboard

### New Prompt Page
1. Enter a unique name for your prompt
2. Type the prompt content in the textarea
3. Click "Add" to save the prompt
4. Click "Back" to return to the main page

## Model Fields

- **name**: Unique name for the prompt (max 200 characters)
- **content**: The actual text content of the prompt
- **created_at**: Timestamp when the prompt was created
- **updated_at**: Timestamp when the prompt was last updated

## Notes

- Prompt names must be unique
- If a prompt with the same name exists, it will be updated instead of creating a duplicate
- The first prompt in the database is loaded by default on page load
- The copy functionality works with modern browsers (uses Clipboard API with fallback)

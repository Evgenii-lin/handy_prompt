from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.conf import settings
import os
from .models import Prompt


def main_page(request):
    """Main page with dropdown menu, textarea, and copy button."""
    prompts = Prompt.objects.all()

    # Get unique prompts (first occurrence of each name)
    unique_prompts = {}
    for prompt in prompts.order_by('name', 'id'):
        if prompt.name not in unique_prompts:
            unique_prompts[prompt.name] = prompt
    unique_prompts_list = list(unique_prompts.values())

    # Check for duplicate prompt names
    prompt_names = [prompt.name for prompt in prompts]
    duplicate_names = set(name for name in prompt_names if prompt_names.count(name) > 1)

    # Create a dictionary to track which prompts have duplicate names
    duplicate_prompts = set()
    for name in duplicate_names:
        for prompt in prompts.filter(name=name):
            duplicate_prompts.add(prompt.id)

    # Get the first prompt's content as default
    default_content = ''
    default_prompt_name = 'Select a Prompt'

    if unique_prompts_list:
        first_prompt = unique_prompts_list[0]
        default_content = first_prompt.content
        default_prompt_name = first_prompt.name

    context = {
        'prompts': unique_prompts_list,  # Only show unique prompts in dropdown
        'duplicate_prompts': duplicate_prompts,
        'duplicate_names': list(duplicate_names),
        'default_content': default_content,
        'default_prompt_name': default_prompt_name,
    }
    return render(request, 'prompt_app/main_paige.html', context)


def new_prompt(request):
    """Page to add a new prompt."""
    if request.method == 'POST':
        prompt_name = request.POST.get('prompt_name')
        prompt_content = request.POST.get('prompt_content')

        if prompt_name and prompt_content:
            # Check if prompt name already exists
            existing_prompt = Prompt.objects.filter(name=prompt_name).first()
            if existing_prompt:
                return render(request, 'prompt_app/new_prompt.html', {
                    'error': 'A prompt with this name already exists. Please use a unique name or edit the existing one.'
                })
            else:
                # Create new prompt
                Prompt.objects.create(name=prompt_name, content=prompt_content)
                message = f"Prompt '{prompt_name}' added successfully!"

                return render(request, 'prompt_app/new_prompt.html', {'message': message})
        else:
            return render(request, 'prompt_app/new_prompt.html', {'error': 'Please fill in all fields.'})

    return render(request, 'prompt_app/new_prompt.html')


def load_prompt(request, prompt_id):
    """AJAX endpoint to load prompt content by ID."""
    prompt = get_object_or_404(Prompt, id=prompt_id)
    return JsonResponse({'content': prompt.content})


def copy_text(request, prompt_id):
    """AJAX endpoint to get text for copying."""
    prompt = get_object_or_404(Prompt, id=prompt_id)
    return JsonResponse({'text': prompt.content})


def edit_prompt(request, prompt_id):
    """Page to edit an existing prompt."""
    prompt = get_object_or_404(Prompt, id=prompt_id)

    if request.method == 'POST':
        prompt_name = request.POST.get('prompt_name')
        prompt_content = request.POST.get('prompt_content')

        if prompt_name and prompt_content:
            # Check if prompt name already exists (but not the current one)
            existing_prompt = Prompt.objects.filter(name=prompt_name).exclude(id=prompt_id).first()
            if existing_prompt:
                return render(request, 'prompt_app/edit_prompt.html', {
                    'prompt': prompt,
                    'error': 'A prompt with this name already exists. Please use a unique name.'
                })

            # Update the prompt
            prompt.name = prompt_name
            prompt.content = prompt_content
            prompt.save()
            return redirect('main_page')
        else:
            return render(request, 'prompt_app/edit_prompt.html', {
                'prompt': prompt,
                'error': 'Please fill in all fields.'
            })

    return render(request, 'prompt_app/edit_prompt.html', {'prompt': prompt})


def delete_prompt(request, prompt_id):
    """Delete a prompt (AJAX endpoint)."""
    prompt = get_object_or_404(Prompt, id=prompt_id)

    if request.method in ['POST', 'DELETE']:
        prompt_name = prompt.name
        prompt.delete()
        return JsonResponse({'success': True, 'message': f'Prompt "{prompt_name}" deleted successfully.'})
    else:
        return JsonResponse({'error': 'Invalid request method.'}, status=400)


def cleanup_duplicates(request):
    """Page to identify and optionally clean up duplicate prompt names."""
    # Find duplicate names
    prompt_names = list(Prompt.objects.values_list('name', flat=True))
    duplicates = {}
    seen = set()
    for name in prompt_names:
        if name in seen:
            if name not in duplicates:
                duplicates[name] = []
            duplicates[name].append(name)
        else:
            seen.add(name)

    # Get all prompts with duplicate names
    duplicate_prompt_ids = set()
    for name in duplicates.keys():
        for prompt in Prompt.objects.filter(name=name):
            duplicate_prompt_ids.add(prompt.id)

    duplicate_prompts = Prompt.objects.filter(id__in=duplicate_prompt_ids).order_by('name', 'id')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete_duplicates':
            ids_to_delete = request.POST.getlist('prompt_ids')
            for prompt_id in ids_to_delete:
                prompt = Prompt.objects.filter(id=prompt_id).first()
                if prompt:
                    prompt.delete()
            return render(request, 'prompt_app/cleanup_duplicates.html', {
                'message': 'Selected duplicate prompts deleted successfully!',
                'duplicates': duplicates,
                'duplicate_prompts': Prompt.objects.filter(id__in=duplicate_prompt_ids).order_by('name', 'id')
            })

    return render(request, 'prompt_app/cleanup_duplicates.html', {
        'duplicates': duplicates,
        'duplicate_prompts': duplicate_prompts,
        'has_duplicates': len(duplicates) > 0
    })


def extract_prompt(request):
    """AJAX endpoint to extract and save prompt to a text file."""
    if request.method == 'POST':
        import json
        try:
            data = json.loads(request.body)
            prompt_name = data.get('prompt_name', 'untitled')
            content = data.get('content', '')

            if not content:
                return JsonResponse({'success': False, 'error': 'No content to extract'})

            # Sanitize the prompt name for use as a filename
            # Replace spaces with underscores and remove special characters
            safe_name = prompt_name.replace(' ', '_')
            safe_name = ''.join(c for c in safe_name if c.isalnum() or c in '_-')

            # Create output directory if it doesn't exist
            output_dir = os.path.join(settings.BASE_DIR, 'extracted_prompts')
            os.makedirs(output_dir, exist_ok=True)

            # Define the file path
            file_path = os.path.join(output_dir, f"{safe_name}.txt")

            # Write the content to the file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return JsonResponse({
                'success': True,
                'file_path': file_path,
                'message': f"Prompt '{prompt_name}' saved successfully"
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'error': 'Invalid request method.'}, status=400)


def extract_all_prompts(request):
    """AJAX endpoint to extract and save all prompts to text files."""
    if request.method == 'POST':
        import json
        try:
            data = json.loads(request.body)
            prompt_names = data.get('prompt_names', [])

            if not prompt_names:
                return JsonResponse({'success': False, 'error': 'No prompts to extract'})

            # Create output directory if it doesn't exist
            output_dir = os.path.join(settings.BASE_DIR, 'extracted_prompts')
            os.makedirs(output_dir, exist_ok=True)

            extracted_count = 0
            errors = []

            for prompt_name in prompt_names:
                # Sanitize the prompt name for use as a filename
                safe_name = prompt_name.replace(' ', '_')
                safe_name = ''.join(c for c in safe_name if c.isalnum() or c in '_-')

                # Get the first prompt with this name
                prompt = Prompt.objects.filter(name=prompt_name).first()
                if not prompt:
                    errors.append(f"Prompt '{prompt_name}' not found")
                    continue

                # Define the file path
                file_path = os.path.join(output_dir, f"{safe_name}.txt")

                # Write the content to the file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(prompt.content)

                extracted_count += 1

            return JsonResponse({
                'success': True,
                'count': extracted_count,
                'file_path': output_dir,
                'errors': errors if errors else None,
                'message': f"Extracted {extracted_count} prompts successfully"
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'error': 'Invalid request method.'}, status=400)

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from . import db, login_manager
from .models import User, Project, Task, ProjectAccess
from .forms import RegistrationForm, LoginForm, ProjectForm, TaskForm
from werkzeug.security import generate_password_hash, check_password_hash

bp = Blueprint('main', __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user = User(username=form.username.data, email=form.email.data, password_hash=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('main.login'))
    return render_template('register.html', form=form)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not check_password_hash(user.password_hash, form.password.data):
            flash('Invalid email or password')
            return redirect(url_for('main.login'))
        login_user(user)
        return redirect(url_for('main.dashboard'))
    return render_template('login.html', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.login'))

@bp.route('/dashboard')
@login_required
def dashboard():
    user_projects = Project.query.filter_by(user_id=current_user.id).all()
    shared_projects = [access.project for access in current_user.accessible_projects]
    form = ProjectForm()
    return render_template('dashboard.html', projects=user_projects, shared_projects=shared_projects, form=form)

@bp.route('/projects', methods=['POST'])
@login_required
def create_project():
    form = ProjectForm()
    if form.validate_on_submit():
        project = Project(name=form.name.data, owner=current_user)
        db.session.add(project)
        db.session.commit()
        if form.share_with.data:
            emails = [email.strip() for email in form.share_with.data.split(',')]
            for email in emails:
                user = User.query.filter_by(email=email).first()
                if user:
                    project_access = ProjectAccess(project_id=project.id, user_id=user.id)
                    db.session.add(project_access)
        db.session.commit()
        flash('Project created successfully!')
    return redirect(url_for('main.dashboard'))

@bp.route('/project/<int:project_id>')
@login_required
def project(project_id):
    project = Project.query.get_or_404(project_id)
    if project.owner != current_user and not ProjectAccess.query.filter_by(project_id=project_id, user_id=current_user.id).first():
        flash('You do not have permission to view this project.')
        return redirect(url_for('main.dashboard'))
    
    form = TaskForm()
    project_users = [project.owner] + [access.user for access in project.shared_with]
    form.assignee.choices = [(user.id, user.username) for user in project_users]
    
    return render_template('project.html', project=project, form=form, project_users=project_users)


@bp.route('/project/<int:project_id>/add_task', methods=['POST'])
@login_required
def add_task(project_id):
    project = Project.query.get_or_404(project_id)
    if project.owner != current_user and not ProjectAccess.query.filter_by(project_id=project_id, user_id=current_user.id).first():
        flash('You do not have permission to add tasks to this project.')
        return redirect(url_for('main.dashboard'))
    
    form = TaskForm()
    form.assignee.choices = [(user.id, user.username) for user in [project.owner] + [access.user for access in project.shared_with]]
    
    if form.validate_on_submit():
        task = Task(
            title=form.title.data, 
            description=form.description.data, 
            project=project,
            assignee_id=form.assignee.data if form.assignee.data != 'None' else None
        )
        db.session.add(task)
        db.session.commit()
        flash('Task added successfully!')
    return redirect(url_for('main.project', project_id=project_id))

@bp.route('/update_task_status/<int:task_id>', methods=['POST'])
@login_required
def update_task_status(task_id):
    task = Task.query.get_or_404(task_id)
    if task.project.owner != current_user and not ProjectAccess.query.filter_by(project_id=task.project_id, user_id=current_user.id).first():
        return jsonify({'success': False}), 403
    data = request.get_json()
    task.status = data['status']
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/update_task_assignee/<int:task_id>', methods=['POST'])
@login_required
def update_task_assignee(task_id):
    task = Task.query.get_or_404(task_id)
    if task.project.owner != current_user and not ProjectAccess.query.filter_by(project_id=task.project_id, user_id=current_user.id).first():
        flash('You do not have permission to update this task.')
        return redirect(url_for('main.project', project_id=task.project_id))
    
    assignee_id = request.form.get('assignee')
    if assignee_id:
        task.assignee_id = assignee_id
        db.session.commit()
        flash('Task assignee updated successfully!')
    else:
        flash('Invalid assignee.')
    
    return redirect(url_for('main.project', project_id=task.project_id))

@bp.route('/get_task_description/<int:task_id>', methods=['GET'])
@login_required
def get_task_description(task_id):
    task = Task.query.get_or_404(task_id)
    if task.project.owner != current_user and not ProjectAccess.query.filter_by(project_id=task.project_id, user_id=current_user.id).first():
        return jsonify({'success': False}), 403
    return jsonify({'title': task.title, 'description': task.description, 'assignee_id': task.assignee_id})

@bp.route('/delete_task/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    project_id = task.project.id
    if task.project.owner != current_user and not ProjectAccess.query.filter_by(project_id=task.project_id, user_id=current_user.id).first():
        return jsonify({'success': False}), 403
    db.session.delete(task)
    db.session.commit()
    flash('Task deleted successfully!')
    return jsonify({'success': True})

@bp.route('/share_project/<int:project_id>', methods=['POST'])
@login_required
def share_project(project_id):
    project = Project.query.get_or_404(project_id)
    if project.owner != current_user:
        flash('You do not have permission to share this project.')
        return redirect(url_for('main.dashboard'))
    
    email = request.form.get('email')
    user = User.query.filter_by(email=email).first()
    if user:
        project_access = ProjectAccess(project_id=project.id, user_id=user.id)
        db.session.add(project_access)
        db.session.commit()
        flash('Project shared successfully!')
    else:
        flash('User with this email does not exist.')
    
    return redirect(url_for('main.project', project_id=project_id))

@bp.route('/delete_project/<int:project_id>', methods=['POST'])
@login_required
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    if project.owner != current_user:
        flash('You do not have permission to delete this project.')
        return redirect(url_for('main.dashboard'))
    
    # Удаление задач проекта
    for task in project.tasks:
        db.session.delete(task)
    
    # Удаление доступа других пользователей
    ProjectAccess.query.filter_by(project_id=project.id).delete()
    
    db.session.delete(project)
    db.session.commit()
    flash('Project deleted successfully!')
    return redirect(url_for('main.dashboard'))

document.addEventListener('DOMContentLoaded', function() {
    const tasks = document.querySelectorAll('.kanban-task');
    const columns = document.querySelectorAll('.kanban-tasks');
    const modal = document.getElementById('taskDescriptionModal');
    const modalTitle = modal.querySelector('.modal-title');
    const modalBody = modal.querySelector('.modal-body');
    const deleteTaskBtn = document.getElementById('deleteTaskBtn');
    
    let currentTaskId = null;
    
    tasks.forEach(task => {
        task.draggable = true;
        task.addEventListener('dragstart', dragStart);
        task.addEventListener('dragend', dragEnd);
        task.addEventListener('dblclick', () => {
            currentTaskId = task.id.split('-')[1];
            fetch(`/get_task_description/${currentTaskId}`)
                .then(response => response.json())
                .then(data => {
                    modalTitle.textContent = data.title;
                    modalBody.textContent = data.description;
                    $('#taskDescriptionModal').modal('show');
                });
        });
    });

    deleteTaskBtn.addEventListener('click', () => {
        if (currentTaskId) {
            fetch(`/delete_task/${currentTaskId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById(`task-${currentTaskId}`).remove();
                    $('#taskDescriptionModal').modal('hide');  // Закрытие модального окна
                } else {
                    console.error('Error deleting task');
                }
            });
        }
    });

    columns.forEach(column => {
        column.addEventListener('dragover', dragOver);
        column.addEventListener('dragenter', dragEnter);
        column.addEventListener('dragleave', dragLeave);
        column.addEventListener('drop', drop);
    });

    function dragStart(e) {
        e.dataTransfer.setData('text/plain', e.target.id);
        setTimeout(() => {
            e.target.classList.add('hide');
        }, 0);
    }

    function dragEnd(e) {
        e.target.classList.remove('hide');
    }

    function dragOver(e) {
        e.preventDefault();
    }

    function dragEnter(e) {
        e.preventDefault();
        e.target.classList.add('drag-over');
    }

    function dragLeave(e) {
        e.target.classList.remove('drag-over');
    }

    function drop(e) {
        e.target.classList.remove('drag-over');

        const id = e.dataTransfer.getData('text/plain');
        const draggable = document.getElementById(id);
        if (draggable && e.target.classList.contains('kanban-tasks')) {
            e.target.appendChild(draggable);

            // Update task status in the database and in the UI
            const status = e.target.id.split('-')[0];
            updateTaskStatus(id.split('-')[1], status);
            const statusBadge = draggable.querySelector('.badge');
            statusBadge.textContent = status.charAt(0).toUpperCase() + status.slice(1);
            if (status === 'todo') {
                statusBadge.className = 'badge bg-primary';
            } else if (status === 'inprogress') {
                statusBadge.className = 'badge bg-warning';
            } else if (status === 'done') {
                statusBadge.className = 'badge bg-success';
            }
        }
    }

    function updateTaskStatus(taskId, status) {
        fetch(`/update_task_status/${taskId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ status: status }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log('Task status updated successfully');
            } else {
                console.error('Error updating task status');
            }
        });
    }
});

document.addEventListener('DOMContentLoaded', function() {
    const tasks = document.querySelectorAll('.kanban-task');
    const columns = document.querySelectorAll('.kanban-tasks');

    tasks.forEach(task => {
        task.draggable = true;
        task.addEventListener('dragstart', dragStart);
        task.addEventListener('dragend', dragEnd);
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

            // Update task status in the database
            const status = e.target.id.split('-')[0];
            updateTaskStatus(id.split('-')[1], status);
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

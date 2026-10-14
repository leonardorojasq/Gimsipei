// Classes Management JavaScript
// Used by: teacher/teacher_classes.html, teacher/grades_view.html
// Owns: expand/collapse rows, auto-close alerts, class create modal,
//       file input previews, modal background close. Resource modal
//       helpers live in resources_view.js (do not duplicate them here).

// Initialize expand/collapse functionality for course rows
function initializeExpandButtons() {
    const expandButtons = document.querySelectorAll('.expand-btn');

    expandButtons.forEach(button => {
        button.addEventListener('click', function() {
            const courseId = this.getAttribute('data-course-id');
            const courseRow = this.closest('.course-row');
            const expandableRow = document.querySelector(`.expandable-row[data-course-id="${courseId}"]`);
            const icon = this.querySelector('i');

            if (!expandableRow) return;

            // Toggle expanded state
            const isExpanded = expandableRow.classList.contains('show');

            if (isExpanded) {
                expandableRow.classList.remove('show');
                expandableRow.style.display = 'none';
                courseRow.classList.remove('expanded');
                if (icon) {
                    icon.classList.remove('fa-chevron-up');
                    icon.classList.add('fa-chevron-down');
                }
            } else {
                expandableRow.classList.add('show');
                expandableRow.style.display = 'table-row';
                courseRow.classList.add('expanded');
                if (icon) {
                    icon.classList.remove('fa-chevron-down');
                    icon.classList.add('fa-chevron-up');
                }
            }
        });
    });
}

// Period functionality removed - no longer needed

// Open Create Class Modal
function openCreateClassModal(courseId, subjectId, subjectName) {
    const modal = document.getElementById('createClassModal');

    // Set hidden fields
    document.getElementById('class_course_id').value = courseId;
    document.getElementById('class_subject_id').value = subjectId;

    // Show modal
    modal.style.display = 'flex';

    // Reset form
    document.getElementById('createClassForm').reset();
    document.getElementById('class_cover_name').textContent = '';
}

// Close Create Class Modal
function closeCreateClassModal() {
    const modal = document.getElementById('createClassModal');
    modal.style.display = 'none';
    document.getElementById('createClassForm').reset();
    document.getElementById('class_cover_name').textContent = '';
}

// Handle file input changes
function initializeFileInputs() {
    // Class cover image
    const classCoverInput = document.getElementById('class_cover');
    if (classCoverInput) {
        classCoverInput.addEventListener('change', function() {
            const fileName = this.files[0] ? this.files[0].name : '';
            document.getElementById('class_cover_name').textContent = fileName;
        });
    }

    // Resource file
    const resourceFileInput = document.getElementById('resource_file');
    if (resourceFileInput) {
        resourceFileInput.addEventListener('change', function() {
            const fileName = this.files[0] ? this.files[0].name : '';
            document.getElementById('resource_file_name').textContent = fileName;
        });
    }
}

// Close modal when clicking outside
function initializeModalBackgroundClose() {
    document.getElementById('createClassModal')?.addEventListener('click', function(e) {
        if (e.target === this) {
            closeCreateClassModal();
        }
    });

    // Resource modal background close is handled in resources_view.js
}

// Auto close alerts after 5 seconds
function initializeAutoCloseAlerts() {
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');

    alerts.forEach(alert => {
        setTimeout(() => {
            if (typeof bootstrap !== 'undefined' && bootstrap.Alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            } else {
                const closeBtn = alert.querySelector('.btn-close');
                if (closeBtn) {
                    closeBtn.click();
                } else {
                    alert.style.display = 'none';
                }
            }
        }, 5000);
    });
}

// Make class modal functions globally available (used by inline onclick)
window.openCreateClassModal = openCreateClassModal;
window.closeCreateClassModal = closeCreateClassModal;

// DOMContentLoaded initializations
document.addEventListener('DOMContentLoaded', function() {
    initializeExpandButtons();
    initializeAutoCloseAlerts();
    initializeFileInputs();
    initializeModalBackgroundClose();
});

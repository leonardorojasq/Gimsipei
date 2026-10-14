// Resources View JavaScript

document.addEventListener("DOMContentLoaded", function () {
  initializePeriodSelector();
  initializeResourceModal();
  initializeAddFirstResourceButtons();
  initializeDeleteResourceModal();
  initializeLoadingStates();
});

// Capture the original (function-declared) implementations in locals BEFORE
// any window.* re-assignment, so the wrapper functions can dispatch to the
// real implementation without recursively calling themselves. (A direct
// `window.openCreateResourceModal = function(){ return openCreateResourceModal(); }`
// would shadow the original global binding and recurse infinitely.)
const _openCreateResourceModalImpl = openCreateResourceModal;
const _closeCreateResourceModalImpl = closeCreateResourceModal;
const _loadAvailableClassesForResourceModalImpl = loadAvailableClassesForResourceModal;

// Re-export to window so inline onclick handlers in the template (and any
// other script that may have shadowed these globals) always call this
// fully-featured version that loads classes via /api/classes.
window.openCreateResourceModal = function (subjectId = null, period = null) {
  return _openCreateResourceModalImpl(subjectId, period);
};
window.closeCreateResourceModal = function () {
  return _closeCreateResourceModalImpl();
};
window.loadAvailableClassesForResourceModal = function () {
  return _loadAvailableClassesForResourceModalImpl();
};

// Module-scoped AbortController so concurrent calls to
// loadAvailableClassesForResourceModal cancel any in-flight request —
// prevents a slow earlier response from overwriting a newer one and
// leaving the select showing stale data.
let _loadClassesInflight = null;

async function loadAvailableClassesForResourceModal() {
  const courseId = document.getElementById("resource_course_id")?.value;
  const subjectId = document.getElementById("resource_subject_id")?.value;
  const period = document.querySelector(
    '#createResourceModal select[name="period"]',
  )?.value;

  const classSelect = document.getElementById("resource_class_number");
  const submitBtn = document.querySelector(
    '#createResourceForm button[type="submit"]',
  );
  if (!classSelect || !submitBtn) return;

  // Cancel any in-flight request before starting a new one
  if (_loadClassesInflight) {
    try { _loadClassesInflight.abort(); } catch (e) { /* noop */ }
  }
  const inflight = new AbortController();
  _loadClassesInflight = inflight;

  // While loading, show a loading state on the select (without disabling it:
  // we want the user to always be able to submit; the backend will validate
  // the class_id and return a clear error if missing).
  classSelect.innerHTML = '<option value="">CARGANDO CLASES...</option>';

  if (!courseId || !subjectId) {
    classSelect.innerHTML = '<option value="">PRIMERO SELECCIONA UN PERIODO</option>';
    _loadClassesInflight = null;
    return;
  }

  if (!period) {
    classSelect.innerHTML = '<option value="">PRIMERO SELECCIONA UN PERIODO</option>';
    _loadClassesInflight = null;
    return;
  }

  try {
    const response = await fetch(
      `/resources/api/classes?course_id=${encodeURIComponent(courseId)}&subject_id=${encodeURIComponent(subjectId)}&period=${encodeURIComponent(period)}`,
      {
        method: "GET",
        credentials: "same-origin",
        headers: { Accept: "application/json" },
        signal: inflight.signal,
      },
    );

    const payload = await response.json();
    const items = payload?.data?.items || [];

    if (!response.ok || payload?.success === false) {
      classSelect.innerHTML =
        '<option value="">ERROR AL CARGAR CLASES</option>';
      _loadClassesInflight = null;
      return;
    }

    if (!items.length) {
      classSelect.innerHTML =
        '<option value="">NO HAY CLASES EN ESTE PERIODO</option>';
      _loadClassesInflight = null;
      return;
    }

    classSelect.innerHTML = '<option value="">SELECCIONA UNA CLASE</option>';
    items.forEach((item) => {
      const opt = document.createElement("option");
      // El backend de create_resource espera el "número de clase" (class_number), no el id.
      opt.value = String(item.class_number);
      opt.textContent = `CLASE ${item.class_number}${item.title ? ` - ${item.title}` : ""}`;
      classSelect.appendChild(opt);
    });
    _loadClassesInflight = null;
  } catch (e) {
    if (e.name === "AbortError") {
      // A newer request superseded us — leave the select as-is, the newer
      // call will populate it.
      return;
    }
    classSelect.innerHTML = '<option value="">ERROR AL CARGAR CLASES</option>';
    _loadClassesInflight = null;
  }
}

// Period Selector Functionality
function initializePeriodSelector() {
  const periodBtns = document.querySelectorAll(".period-btn");
  const periodContents = document.querySelectorAll(".period-content");

  periodBtns.forEach((btn) => {
    btn.addEventListener("click", function () {
      const period = this.getAttribute("data-period");

      // Remove active class from all buttons
      periodBtns.forEach((b) => b.classList.remove("active"));

      // Add active class to clicked button
      this.classList.add("active");

      // Hide all period contents
      periodContents.forEach((content) => {
        content.style.display = "none";
      });

      // Show selected period content
      const selectedContents = document.querySelectorAll(
        `.period-content[data-period="${period}"]`,
      );
      selectedContents.forEach((content) => {
        content.style.display = "flex";
      });
    });
  });
}

// Resource Modal Functions
function openCreateResourceModal(subjectId = null, period = null) {
  const modal = document.getElementById("createResourceModal");
  if (!modal) return;

  modal.style.display = "flex";

  // Read course_id and subject_id from URL query params first (so the modal
  // works when opened from /resources?course_id=29&subject_id=42).
  const urlParams = new URLSearchParams(window.location.search);
  const urlCourseId = urlParams.get("course_id");
  const urlSubjectId = urlParams.get("subject_id");

  const subjectSection = subjectId || urlSubjectId
    ? document.querySelector(`.subject-section[data-subject-id="${subjectId || urlSubjectId}"]`)
    : document.querySelector(".subject-section");

  if (subjectSection) {
    const courseId = subjectSection.getAttribute("data-course-id");
    const actualSubjectId =
      subjectId || urlSubjectId || subjectSection.getAttribute("data-subject-id");

    const courseIdInput = document.getElementById("resource_course_id");
    const subjectIdInput = document.getElementById("resource_subject_id");

    if (courseIdInput) courseIdInput.value = courseId || urlCourseId || "";
    if (subjectIdInput) subjectIdInput.value = actualSubjectId || "";
  } else if (urlCourseId || urlSubjectId) {
    // URL has course_id/subject_id but there's no matching subject-section in
    // the DOM. Use the URL values directly.
    const courseIdInput = document.getElementById("resource_course_id");
    const subjectIdInput = document.getElementById("resource_subject_id");
    if (courseIdInput) courseIdInput.value = urlCourseId || "";
    if (subjectIdInput) subjectIdInput.value = urlSubjectId || "";
  }

  // Configure period: explicit arg > active period button > empty
  const periodSelect = document.querySelector(
    '#createResourceModal select[name="period"]',
  );
  if (periodSelect) {
    periodSelect.value =
      period ||
      document
        .querySelector(".period-btn.active")
        ?.getAttribute("data-period") ||
      "";
  }

  // Load available classes for the period/course/subject
  loadAvailableClassesForResourceModal();
}

function closeCreateResourceModal() {
  const modal = document.getElementById("createResourceModal");
  if (!modal) return;

  modal.style.display = "none";

  const form = document.getElementById("createResourceForm");
  if (form) {
    form.reset();
    document.querySelectorAll(".file-name").forEach((display) => {
      display.textContent = "";
    });
  }

  // Reset select state
  const classSelect = document.getElementById("resource_class_number");
  const submitBtn = document.querySelector(
    '#createResourceForm button[type="submit"]',
  );
  if (classSelect) {
    classSelect.innerHTML = '<option value="">SELECCIONA UNA CLASE</option>';
  }
  if (submitBtn) submitBtn.disabled = false;
}

// Initialize "Add First Resource" buttons
function initializeAddFirstResourceButtons() {
  document.querySelectorAll(".btn-add-first-resource").forEach((btn) => {
    btn.addEventListener("click", function () {
      openCreateResourceModal(
        this.getAttribute("data-subject-id"),
        this.getAttribute("data-period"),
      );
    });
  });
}

function initializeResourceModal() {
  const modal = document.getElementById("createResourceModal");
  if (!modal) return;

  // Close modal when clicking outside
  modal.addEventListener("click", function (e) {
    if (e.target === modal) {
      closeCreateResourceModal();
    }
  });

  // File input display names
  const coverImageInput = document.getElementById("resource_cover_image");
  const resourceFileInput = document.getElementById("resource_file");
  const periodSelect = document.querySelector(
    '#createResourceModal select[name="period"]',
  );

  if (coverImageInput) {
    coverImageInput.addEventListener("change", function () {
      const fileNameDisplay = document.getElementById(
        "resource_cover_image_name",
      );
      if (fileNameDisplay) {
        fileNameDisplay.textContent = this.files[0]?.name || "";
      }
    });
  }

  if (resourceFileInput) {
    resourceFileInput.addEventListener("change", function () {
      const fileNameDisplay = document.getElementById("resource_file_name");
      if (fileNameDisplay) {
        fileNameDisplay.textContent = this.files[0]?.name || "";
      }
    });
  }

  if (periodSelect) {
    periodSelect.addEventListener("change", function () {
      loadAvailableClassesForResourceModal();
    });
  }

  // Handle ESC key to close modal
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      closeCreateResourceModal();
    }
  });
}

// Delete Resource Modal Functionality
function initializeDeleteResourceModal() {
  initializeDeleteButtons(".open-delete-resource-modal", function (button) {
    const resourceId = button.getAttribute("data-resource-id");
    return `/resources/${resourceId}/delete`;
  });
}

// Loading States Functions
function showLoadingState(button, loadingText = "Procesando...") {
  if (!button) return;

  button.disabled = true;
  button.setAttribute("data-original-text", button.innerHTML);
  button.innerHTML = `<i class="fas fa-spinner fa-spin me-2"></i>${loadingText}`;
}

function hideLoadingState(button) {
  if (!button) return;

  const originalText = button.getAttribute("data-original-text");
  if (originalText) {
    button.innerHTML = originalText;
    button.removeAttribute("data-original-text");
  }
  button.disabled = false;
}

// Initialize loading states for create and delete forms
function initializeLoadingStates() {
  const createForm = document.getElementById("createResourceForm");
  const deleteForm = document.getElementById("deleteConfirmationForm");

  if (createForm) {
    createForm.addEventListener("submit", function () {
      const submitBtn = this.querySelector('button[type="submit"]');
      if (submitBtn) showLoadingState(submitBtn, "Guardando...");
    });
  }

  if (deleteForm) {
    deleteForm.addEventListener("submit", function () {
      const submitBtn = this.querySelector('button[type="submit"]');
      if (submitBtn) showLoadingState(submitBtn, "Eliminando...");
    });
  }
}

// Alert auto-dismiss
setTimeout(function () {
  const alerts = document.querySelectorAll(".alert");
  alerts.forEach((alert) => {
    alert.style.transition = "opacity 0.5s ease";
    alert.style.opacity = "0";
    setTimeout(() => alert.remove(), 500);
  });
}, 5000);

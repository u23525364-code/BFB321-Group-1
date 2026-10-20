// Shared dashboard scripts, loaded on every page by base.html.

// Read a theme token from halfway-theme.css, e.g. cssVar('--chart-1')
const cssVar = name => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

// Chart.js defaults (halfway-dashboard skill, section 6)
if (window.Chart) {
  Chart.defaults.font.family = 'Montserrat, system-ui, sans-serif';
  Chart.defaults.font.size = 12;
  Chart.defaults.color = cssVar('--hw-muted');
  Chart.defaults.borderColor = cssVar('--chart-grid');
  Chart.defaults.maintainAspectRatio = false;
  Chart.defaults.plugins.tooltip.backgroundColor = cssVar('--hw-charcoal');
  Chart.defaults.plugins.tooltip.padding = 10;
  Chart.defaults.plugins.tooltip.cornerRadius = 8;
  Chart.defaults.plugins.legend.labels.usePointStyle = true;
}

// Column sorting. Any <th class="sortable-header"> gets a button inside it, so
// sorting works by keyboard as well as mouse. Click toggles ascending / descending.
// Compares cell text, treating numbers numerically ("9 min" < "10 min").
function sortTable(header) {
  const table = header.closest('table');
  const columnIndex = header.cellIndex;
  const tbody = table.tBodies[0];
  const dir = header.getAttribute('aria-sort') === 'ascending' ? 'descending' : 'ascending';

  const rows = Array.from(tbody.rows);
  rows.sort((a, b) => {
    const x = a.cells[columnIndex].textContent.trim();
    const y = b.cells[columnIndex].textContent.trim();
    const result = x.localeCompare(y, undefined, { numeric: true, sensitivity: 'base' });
    return dir === 'ascending' ? result : -result;
  });
  rows.forEach(row => tbody.appendChild(row));

  header.parentElement.querySelectorAll('th').forEach(cell => cell.removeAttribute('aria-sort'));
  header.setAttribute('aria-sort', dir);
}

document.querySelectorAll('th.sortable-header').forEach(header => {
  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'sort-button';
  button.append(...header.childNodes);
  header.appendChild(button);
  button.addEventListener('click', () => sortTable(header));
});

// Short confirmation message in the bottom-right corner (replaces alert()).
function showToast(message) {
  const container = document.getElementById('toastContainer');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = 'toast align-items-center border-0';
  toast.setAttribute('role', 'status');
  toast.setAttribute('aria-live', 'polite');
  toast.innerHTML = '<div class="d-flex"><div class="toast-body"><i class="bi bi-check-circle me-2" aria-hidden="true"></i></div>'
    + '<button type="button" class="btn-close me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button></div>';
  toast.querySelector('.toast-body').append(message);
  container.appendChild(toast);
  toast.addEventListener('hidden.bs.toast', () => toast.remove());
  bootstrap.Toast.getOrCreateInstance(toast).show();
}

// Client-side validation for every <form class="needs-validation" novalidate>.
// Invalid: block submit, show Bootstrap feedback and focus the first problem field.
// Valid with data-success: no backend yet, so confirm with a toast, close any
// surrounding modal and reset. Valid without data-success: submit normally.
document.querySelectorAll('form.needs-validation').forEach(form => {
  form.addEventListener('submit', event => {
    if (!form.checkValidity()) {
      event.preventDefault();
      event.stopPropagation();
      form.classList.add('was-validated');
      form.querySelector(':invalid')?.focus();
      return;
    }
    if (form.dataset.success) {
      event.preventDefault();
      showToast(form.dataset.success);
      const modal = form.closest('.modal');
      if (modal) bootstrap.Modal.getInstance(modal)?.hide();
      form.reset();
      form.classList.remove('was-validated');
    }
  });
});

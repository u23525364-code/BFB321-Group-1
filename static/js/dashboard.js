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

// Column sorting: click a .sortable-header to toggle ascending / descending.
// Compares cell text, treating numbers numerically ("9 min" < "10 min").
function sortTable(columnIndex, tableId) {
  const table = document.getElementById(tableId);
  const tbody = table.tBodies[0];
  const header = table.tHead.rows[0].cells[columnIndex];
  const dir = header.getAttribute('aria-sort') === 'ascending' ? 'descending' : 'ascending';

  const rows = Array.from(tbody.rows);
  rows.sort((a, b) => {
    const x = a.cells[columnIndex].textContent.trim();
    const y = b.cells[columnIndex].textContent.trim();
    const result = x.localeCompare(y, undefined, { numeric: true, sensitivity: 'base' });
    return dir === 'ascending' ? result : -result;
  });
  rows.forEach(row => tbody.appendChild(row));

  Array.from(table.tHead.rows[0].cells).forEach(cell => cell.removeAttribute('aria-sort'));
  header.setAttribute('aria-sort', dir);
}

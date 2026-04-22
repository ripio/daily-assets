// Sidebar toggle (mobile)
document.getElementById('sidebarToggle')?.addEventListener('click', () => {
  document.getElementById('sidebar').classList.toggle('open');
});
document.addEventListener('click', (e) => {
  const sidebar = document.getElementById('sidebar');
  const toggle = document.getElementById('sidebarToggle');
  if (sidebar && toggle && !sidebar.contains(e.target) && !toggle.contains(e.target)) {
    sidebar.classList.remove('open');
  }
});

// Collapse/expand a type's asset children
function toggleGroup(key) {
  const rows = document.querySelectorAll(`[data-parent="${key}"]`);
  const icon = document.getElementById(`icon-${key}`);
  if (!rows.length) return;
  const isOpen = rows[0].style.display !== 'none';
  rows.forEach(r => { r.style.display = isOpen ? 'none' : ''; });
  if (icon) icon.textContent = isOpen ? '▶' : '▼';
}

// Collapse/expand an entire category (all types + their assets)
function toggleCategory(catKey) {
  const rows = document.querySelectorAll(`[data-cat="${catKey}"]`);
  const icon = document.getElementById(`icon-cat-${catKey}`);
  if (!rows.length) return;

  const isOpen = rows[0].style.display !== 'none';

  if (isOpen) {
    rows.forEach(r => { r.style.display = 'none'; });
    if (icon) icon.textContent = '▶';
  } else {
    rows.forEach(r => {
      // Asset rows: only show if their parent type is expanded
      const parentKey = r.dataset.parent;
      if (parentKey) {
        const typeIcon = document.getElementById(`icon-${parentKey}`);
        if (typeIcon && typeIcon.textContent === '▶') {
          r.style.display = 'none';
          return;
        }
      }
      r.style.display = '';
    });
    if (icon) icon.textContent = '▼';
  }
}

// Collapse/expand NO LIQUID category breakdown
function toggleNL() {
  const rows = document.querySelectorAll('.row-nl-category');
  const icon = document.getElementById('icon-nl-total');
  if (!rows.length) return;
  const isOpen = rows[0].style.display !== 'none';
  rows.forEach(r => { r.style.display = isOpen ? 'none' : ''; });
  if (icon) icon.textContent = isOpen ? '▶' : '▼';
}

// Auto-dismiss alerts after 6 seconds
document.querySelectorAll('.alert').forEach(alert => {
  setTimeout(() => {
    alert.style.transition = 'opacity 0.4s';
    alert.style.opacity = '0';
    setTimeout(() => alert.remove(), 400);
  }, 6000);
});

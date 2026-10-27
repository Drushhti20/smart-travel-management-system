/**
 * Beyond Horizons — Smart Travel Management Dashboard Script
 * Implements complete Trip CRUD, real-time stats, filtering, and modal management.
 */

// State
let allTrips = [];
let currentUser = null;
let currentViewingTrip = null;

document.addEventListener('DOMContentLoaded', async () => {
  // 1. Authenticate user & load profile
  const authenticated = await initUserProfile();
  if (!authenticated) return;

  // 2. Setup event listeners
  setupDashboardEventListeners();

  // 3. Load trips and statistics
  await loadDashboardData();
});

/* ==========================================================================
   User Profile & Session
   ========================================================================== */
async function initUserProfile() {
  try {
    const res = await fetch('/api/auth/me', { credentials: 'include' });
    if (!res.ok) throw new Error('Session invalid');

    const data = await res.json();
    if (!data.authenticated || !data.user) {
      window.location.replace('/login');
      return false;
    }

    currentUser = data.user;

    // Update UI elements with actual user's name
    const navName = document.getElementById('user-nav-name');
    const welcomeName = document.getElementById('welcome-user-name');
    const userAvatar = document.getElementById('user-avatar');

    if (navName) navName.textContent = currentUser.name;
    if (welcomeName) welcomeName.textContent = currentUser.name.split(' ')[0] || currentUser.name;
    if (userAvatar) {
      const initial = (currentUser.name || 'U').trim().charAt(0).toUpperCase();
      userAvatar.textContent = initial;
    }

    return true;
  } catch (err) {
    window.location.replace('/login');
    return false;
  }
}

/* ==========================================================================
   Event Listeners Setup
   ========================================================================== */
function setupDashboardEventListeners() {
  // Logout
  const logoutBtn = document.getElementById('btn-logout');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', handleLogout);
  }

  // Open Create Modal buttons
  const openCreateBtns = [
    document.getElementById('btn-open-create-modal'),
    document.getElementById('btn-banner-new-trip'),
    document.getElementById('btn-empty-create-trip'),
  ];
  openCreateBtns.forEach(btn => {
    if (btn) btn.addEventListener('click', () => openCreateTripModal());
  });

  // Modal Close buttons
  document.querySelectorAll('[data-close-modal]').forEach(btn => {
    btn.addEventListener('click', () => {
      const modalId = btn.getAttribute('data-close-modal');
      closeModal(modalId);
    });
  });

  // Close modals on backdrop click or Escape key
  document.querySelectorAll('.modal-backdrop').forEach(modal => {
    modal.addEventListener('click', (event) => {
      if (event.target === modal) {
        closeModal(modal.id);
      }
    });
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal-backdrop.active').forEach(modal => {
        closeModal(modal.id);
      });
    }
  });

  // Create Trip Form Submit
  const createForm = document.getElementById('create-trip-form');
  if (createForm) {
    createForm.addEventListener('submit', handleCreateTripSubmit);
  }

  // Edit Trip Form Submit
  const editForm = document.getElementById('edit-trip-form');
  if (editForm) {
    editForm.addEventListener('submit', handleEditTripSubmit);
  }

  // Confirm Delete Action
  const confirmDeleteBtn = document.getElementById('btn-confirm-delete-action');
  if (confirmDeleteBtn) {
    confirmDeleteBtn.addEventListener('click', handleConfirmDelete);
  }

  // Quick action buttons in View Modal
  const viewEditBtn = document.getElementById('btn-view-quick-edit');
  if (viewEditBtn) {
    viewEditBtn.addEventListener('click', () => {
      if (currentViewingTrip) {
        closeModal('modal-view-trip');
        openEditTripModal(currentViewingTrip);
      }
    });
  }

  const viewDeleteBtn = document.getElementById('btn-view-quick-delete');
  if (viewDeleteBtn) {
    viewDeleteBtn.addEventListener('click', () => {
      if (currentViewingTrip) {
        closeModal('modal-view-trip');
        openDeleteModal(currentViewingTrip.id, currentViewingTrip.title);
      }
    });
  }

  // Search & Filter
  const searchInput = document.getElementById('trip-search-input');
  if (searchInput) {
    searchInput.addEventListener('input', applyFilters);
  }

  const statusFilter = document.getElementById('trip-status-filter');
  if (statusFilter) {
    statusFilter.addEventListener('change', applyFilters);
  }

  // Date bounds synchronization for Create Form
  const todayStr = new Date().toISOString().split('T')[0];
  const createStart = document.getElementById('create-start-date');
  if (createStart) {
    createStart.setAttribute('min', todayStr);
    createStart.addEventListener('change', () => {
      const createEnd = document.getElementById('create-end-date');
      if (createEnd) {
        createEnd.setAttribute('min', createStart.value);
        if (createEnd.value && createEnd.value < createStart.value) {
          createEnd.value = createStart.value;
        }
      }
    });
  }

  // Date bounds synchronization for Edit Form
  const editStart = document.getElementById('edit-start-date');
  if (editStart) {
    editStart.addEventListener('change', () => {
      const editEnd = document.getElementById('edit-end-date');
      if (editEnd) {
        editEnd.setAttribute('min', editStart.value);
        if (editEnd.value && editEnd.value < editStart.value) {
          editEnd.value = editStart.value;
        }
      }
    });
  }

  // Event Delegation for Trip Card Actions (View, Edit, Delete)
  const tripsContainer = document.getElementById('trips-grid-container');
  if (tripsContainer) {
    tripsContainer.addEventListener('click', (e) => {
      const editBtn = e.target.closest('[data-edit-trip-id]');
      if (editBtn) {
        e.preventDefault();
        const id = editBtn.getAttribute('data-edit-trip-id');
        const trip = allTrips.find(t => String(t.id) === String(id));
        if (trip) openEditTripModal(trip);
        return;
      }

      const viewBtn = e.target.closest('[data-view-trip-id]');
      if (viewBtn) {
        e.preventDefault();
        const id = viewBtn.getAttribute('data-view-trip-id');
        const trip = allTrips.find(t => String(t.id) === String(id));
        if (trip) openViewTripModal(trip);
        return;
      }

      const delBtn = e.target.closest('[data-delete-trip-id]');
      if (delBtn) {
        e.preventDefault();
        const id = delBtn.getAttribute('data-delete-trip-id');
        const trip = allTrips.find(t => String(t.id) === String(id));
        if (trip) openDeleteModal(trip.id, trip.title);
        return;
      }
    });
  }
}

/* ==========================================================================
   Dashboard Data Loading & Rendering
   ========================================================================== */
async function loadDashboardData() {
  const container = document.getElementById('trips-grid-container');
  if (container && allTrips.length === 0) {
    container.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 40px; color: var(--ink-muted);">Loading your journeys…</div>';
  }

  try {
    const [tripsRes, statsRes] = await Promise.all([
      fetch('/api/trips', { credentials: 'include' }),
      fetch('/api/trips/stats', { credentials: 'include' })
    ]);

    if (!tripsRes.ok || !statsRes.ok) {
      throw new Error('Failed to load dashboard data');
    }

    const tripsData = await tripsRes.json();
    const statsData = await statsRes.json();

    allTrips = tripsData.trips || [];

    // Render Stats
    updateStatsUI(statsData.stats || {});

    // Render Trips Grid
    applyFilters();

  } catch (err) {
    showToast('Could not load dashboard itineraries. Please refresh.', 'error');
    if (container && allTrips.length === 0) {
      container.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 40px; color: var(--danger);">Failed to load trips. Please check connection.</div>';
    }
  }
}

function updateStatsUI(stats) {
  const totalElem = document.getElementById('stat-total-trips');
  const upcomingElem = document.getElementById('stat-upcoming-trips');
  const ongoingElem = document.getElementById('stat-ongoing-trips');
  const completedElem = document.getElementById('stat-completed-trips');

  if (totalElem) totalElem.textContent = stats.total_trips || 0;
  if (upcomingElem) upcomingElem.textContent = stats.upcoming_trips || 0;
  if (ongoingElem) ongoingElem.textContent = stats.ongoing_trips || 0;
  if (completedElem) completedElem.textContent = stats.completed_trips || 0;
}

function applyFilters() {
  const searchInput = document.getElementById('trip-search-input');
  const statusFilter = document.getElementById('trip-status-filter');

  const query = (searchInput ? searchInput.value : '').trim().toLowerCase();
  const selectedStatus = statusFilter ? statusFilter.value : 'all';

  const filtered = allTrips.filter(trip => {
    // Text search in destination or title
    const matchesQuery = !query || 
      (trip.destination && trip.destination.toLowerCase().includes(query)) || 
      (trip.title && trip.title.toLowerCase().includes(query));

    // Status filter
    const matchesStatus = selectedStatus === 'all' || 
      (trip.status && trip.status.toLowerCase() === selectedStatus);

    return matchesQuery && matchesStatus;
  });

  renderTrips(filtered);
}

function renderTrips(trips) {
  const container = document.getElementById('trips-grid-container');
  const emptyBox = document.getElementById('empty-state-box');
  if (!container || !emptyBox) return;

  if (allTrips.length === 0) {
    container.innerHTML = '';
    emptyBox.style.display = 'block';
    return;
  }

  emptyBox.style.display = 'none';

  if (trips.length === 0) {
    container.innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; padding: 48px; background: #ffffff; border-radius: 16px; border: 1px dashed var(--border-light);">
        <p style="color: var(--ink-secondary); font-size: 1rem; margin-bottom: 12px;">No trips found matching your filter criteria.</p>
        <button class="btn btn-secondary btn-sm" onclick="clearFilters()">Reset Filter</button>
      </div>
    `;
    return;
  }

  container.innerHTML = trips.map(trip => createTripCardHTML(trip)).join('');
}

function clearFilters() {
  const searchInput = document.getElementById('trip-search-input');
  const statusFilter = document.getElementById('trip-status-filter');
  if (searchInput) searchInput.value = '';
  if (statusFilter) statusFilter.value = 'all';
  applyFilters();
}

function createTripCardHTML(trip) {
  const formattedBudget = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0
  }).format(trip.budget || 0);

  const formattedStart = formatReadableDate(trip.start_date);
  const formattedEnd = formatReadableDate(trip.end_date);
  const statusClass = `status-${(trip.status || 'planned').toLowerCase()}`;

  return `
    <article class="trip-card" data-card-id="${escapeHtml(trip.id)}">
      <div class="trip-card-head">
        <div>
          <span class="trip-dest-tag">📍 ${escapeHtml(trip.destination)}</span>
          <h3 class="trip-card-name">${escapeHtml(trip.title)}</h3>
        </div>
        <span class="status-pill ${statusClass}">${escapeHtml(trip.status)}</span>
      </div>

      <div class="trip-card-body">
        <div class="trip-details-row">
          <div class="trip-info-item">
            <small>Dates</small>
            <span>${formattedStart} – ${formattedEnd}</span>
          </div>
          <div class="trip-info-item">
            <small>Duration</small>
            <span>${trip.duration_days} ${trip.duration_days === 1 ? 'Day' : 'Days'}</span>
          </div>
          <div class="trip-info-item">
            <small>Budget</small>
            <span style="color: var(--blue-primary); font-weight: 700;">${formattedBudget}</span>
          </div>
          <div class="trip-info-item">
            <small>Travelers</small>
            <span>${trip.travelers} ${trip.travelers === 1 ? 'Person' : 'People'}</span>
          </div>
        </div>

        <p class="trip-notes-snippet">
          ${trip.notes ? escapeHtml(trip.notes) : '<em style="color: var(--ink-muted);">No extra notes added.</em>'}
        </p>
      </div>

      <div class="trip-card-foot">
        <button type="button" class="btn btn-secondary btn-sm" data-view-trip-id="${escapeHtml(trip.id)}">
          View
        </button>
        <button type="button" class="btn btn-secondary btn-sm" data-edit-trip-id="${escapeHtml(trip.id)}">
          Edit
        </button>
        <button type="button" class="btn btn-secondary btn-sm" style="color: var(--danger);" data-delete-trip-id="${escapeHtml(trip.id)}">
          Delete
        </button>
      </div>
    </article>
  `;
}

/* ==========================================================================
   Trip CRUD Operations
   ========================================================================== */

// 1. CREATE TRIP
function openCreateTripModal() {
  const form = document.getElementById('create-trip-form');
  if (form) form.reset();

  const alertBox = document.getElementById('create-trip-alert');
  if (alertBox) {
    alertBox.style.display = 'none';
    alertBox.textContent = '';
  }

  // Pre-set start date to tomorrow and end date to 7 days later
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  const nextWeek = new Date();
  nextWeek.setDate(nextWeek.getDate() + 8);

  const startInput = document.getElementById('create-start-date');
  const endInput = document.getElementById('create-end-date');
  if (startInput) startInput.value = tomorrow.toISOString().split('T')[0];
  if (endInput) {
    endInput.value = nextWeek.toISOString().split('T')[0];
    if (startInput) endInput.setAttribute('min', startInput.value);
  }

  openModal('modal-create-trip');
}

async function handleCreateTripSubmit(e) {
  e.preventDefault();
  const alertBox = document.getElementById('create-trip-alert');
  const submitBtn = document.getElementById('btn-save-create-trip');

  const title = document.getElementById('create-title').value.trim();
  const destination = document.getElementById('create-destination').value.trim();
  const startDate = document.getElementById('create-start-date').value;
  const endDate = document.getElementById('create-end-date').value;
  const budget = parseFloat(document.getElementById('create-budget').value);
  const travelers = parseInt(document.getElementById('create-travelers').value, 10);
  const notes = document.getElementById('create-notes').value.trim();

  // Validation
  if (!title || title.length < 2) {
    showFormError(alertBox, 'Trip title must be at least 2 characters.');
    return;
  }
  if (!destination || destination.length < 2) {
    showFormError(alertBox, 'Destination must be at least 2 characters.');
    return;
  }
  if (!startDate || !endDate) {
    showFormError(alertBox, 'Please provide both start and end dates.');
    return;
  }
  if (endDate < startDate) {
    showFormError(alertBox, 'End date cannot be earlier than start date.');
    return;
  }
  if (isNaN(budget) || budget < 0) {
    showFormError(alertBox, 'Budget must be a valid positive number.');
    return;
  }
  if (isNaN(travelers) || travelers < 1) {
    showFormError(alertBox, 'Number of travelers must be at least 1.');
    return;
  }

  setModalBtnLoading(submitBtn, true, 'Saving…');

  try {
    const res = await fetch('/api/trips', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        title,
        destination,
        start_date: startDate,
        end_date: endDate,
        budget,
        travelers,
        notes
      })
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.message || 'Failed to create trip.');
    }

    closeModal('modal-create-trip');
    showToast(`Trip to ${destination} planned successfully!`, 'success');
    await loadDashboardData();

  } catch (err) {
    showFormError(alertBox, err.message);
  } finally {
    setModalBtnLoading(submitBtn, false, 'Save Journey');
  }
}

// 2. VIEW TRIP
function openViewTripModal(trip) {
  if (!trip) return;
  currentViewingTrip = trip;

  const titleElem = document.getElementById('view-trip-title');
  const destElem = document.getElementById('view-trip-destination');
  const statusElem = document.getElementById('view-status-tag');
  const durationElem = document.getElementById('view-duration-badge');
  const datesElem = document.getElementById('view-trip-dates');
  const budgetElem = document.getElementById('view-trip-budget');
  const travelersElem = document.getElementById('view-trip-travelers');
  const idElem = document.getElementById('view-trip-id');
  const notesElem = document.getElementById('view-trip-notes');

  if (titleElem) titleElem.textContent = trip.title;
  if (destElem) destElem.textContent = `📍 ${trip.destination}`;

  if (statusElem) {
    statusElem.textContent = trip.status;
    statusElem.className = `status-pill status-${(trip.status || 'planned').toLowerCase()}`;
  }

  if (durationElem) {
    durationElem.textContent = `${trip.duration_days} ${trip.duration_days === 1 ? 'Day' : 'Days'}`;
  }

  if (datesElem) {
    datesElem.textContent = `${formatReadableDate(trip.start_date)} – ${formatReadableDate(trip.end_date)}`;
  }

  if (budgetElem) {
    budgetElem.textContent = new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(trip.budget || 0);
  }

  if (travelersElem) {
    travelersElem.textContent = `${trip.travelers} ${trip.travelers === 1 ? 'Explorer' : 'Explorers'}`;
  }

  if (idElem) idElem.textContent = `#${trip.id}`;

  if (notesElem) {
    notesElem.textContent = trip.notes || 'No extra notes or itinerary details recorded for this journey.';
  }

  openModal('modal-view-trip');
}

// 3. EDIT TRIP (End-to-End Fix: Pre-population, Clean Date Normalization, and Save Persistence)
function openEditTripModal(trip) {
  if (!trip) return;
  const alertBox = document.getElementById('edit-trip-alert');
  if (alertBox) {
    alertBox.style.display = 'none';
    alertBox.textContent = '';
  }

  const tripId = trip.id || trip._id;
  const idInput = document.getElementById('edit-trip-id');
  if (idInput) idInput.value = tripId;

  const titleInput = document.getElementById('edit-title');
  if (titleInput) titleInput.value = trip.title || '';

  const destInput = document.getElementById('edit-destination');
  if (destInput) destInput.value = trip.destination || '';

  // Clean and normalize dates to strictly YYYY-MM-DD for HTML5 date inputs
  const cleanStartDate = String(trip.start_date || '').split('T')[0].split(' ')[0].trim();
  const cleanEndDate = String(trip.end_date || '').split('T')[0].split(' ')[0].trim();

  const startInput = document.getElementById('edit-start-date');
  const endInput = document.getElementById('edit-end-date');
  if (startInput) startInput.value = cleanStartDate;
  if (endInput) {
    endInput.value = cleanEndDate;
    if (cleanStartDate) {
      endInput.setAttribute('min', cleanStartDate);
    }
  }

  // Parse numerical budget cleanly
  const rawBudget = trip.budget;
  const numBudget = typeof rawBudget === 'number'
    ? rawBudget
    : parseFloat(String(rawBudget || 0).replace(/[^0-9.-]+/g, '')) || 0;
  const budgetInput = document.getElementById('edit-budget');
  if (budgetInput) budgetInput.value = numBudget;

  const travelersInput = document.getElementById('edit-travelers');
  const rawTravelers = trip.travelers !== undefined ? trip.travelers : trip.travellers;
  if (travelersInput) travelersInput.value = parseInt(rawTravelers, 10) || 1;

  const notesInput = document.getElementById('edit-notes');
  if (notesInput) notesInput.value = trip.notes || '';

  openModal('modal-edit-trip');
}

async function handleEditTripSubmit(e) {
  e.preventDefault();
  const alertBox = document.getElementById('edit-trip-alert');
  const submitBtn = document.getElementById('btn-save-edit-trip');

  const tripId = document.getElementById('edit-trip-id').value;
  if (!tripId) {
    showFormError(alertBox, 'Missing trip identifier. Please reopen the edit window.');
    return;
  }

  const title = document.getElementById('edit-title').value.trim();
  const destination = document.getElementById('edit-destination').value.trim();
  const startDate = document.getElementById('edit-start-date').value;
  const endDate = document.getElementById('edit-end-date').value;
  const budget = parseFloat(document.getElementById('edit-budget').value);
  const travelers = parseInt(document.getElementById('edit-travelers').value, 10);
  const notes = document.getElementById('edit-notes').value.trim();

  // Client-Side Validation
  if (!title || title.length < 2) {
    showFormError(alertBox, 'Trip title must be at least 2 characters.');
    return;
  }
  if (!destination || destination.length < 2) {
    showFormError(alertBox, 'Destination must be at least 2 characters.');
    return;
  }
  if (!startDate || !endDate) {
    showFormError(alertBox, 'Please provide both start and end dates.');
    return;
  }
  if (endDate < startDate) {
    showFormError(alertBox, 'End date cannot be earlier than start date.');
    return;
  }
  if (isNaN(budget) || budget < 0) {
    showFormError(alertBox, 'Budget must be a valid positive number.');
    return;
  }
  if (isNaN(travelers) || travelers < 1) {
    showFormError(alertBox, 'Number of travelers must be at least 1.');
    return;
  }

  setModalBtnLoading(submitBtn, true, 'Updating…');

  try {
    const res = await fetch(`/api/trips/${encodeURIComponent(tripId)}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        title,
        destination,
        start_date: startDate,
        end_date: endDate,
        budget,
        travelers,
        notes
      })
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.message || 'Failed to update trip.');
    }

    closeModal('modal-edit-trip');
    showToast(`Trip "${title}" updated successfully!`, 'success');

    // Update locally and update view modal if it was open
    if (data.trip) {
      const idx = allTrips.findIndex(t => String(t.id) === String(tripId));
      if (idx !== -1) {
        allTrips[idx] = data.trip;
      }
      if (currentViewingTrip && String(currentViewingTrip.id) === String(tripId)) {
        currentViewingTrip = data.trip;
      }
      applyFilters();
    }

    // Refresh full dashboard data from database
    await loadDashboardData();

  } catch (err) {
    showFormError(alertBox, err.message);
  } finally {
    setModalBtnLoading(submitBtn, false, 'Save Changes');
  }
}

// 4. DELETE TRIP
function openDeleteModal(tripId, tripTitle) {
  const idInput = document.getElementById('delete-trip-id');
  const labelElem = document.getElementById('delete-trip-title-label');

  if (idInput) idInput.value = tripId;
  if (labelElem) labelElem.textContent = `"${tripTitle}"`;

  openModal('modal-delete-confirm');
}

async function handleConfirmDelete() {
  const tripId = document.getElementById('delete-trip-id').value;
  const btn = document.getElementById('btn-confirm-delete-action');
  if (!tripId) return;

  setModalBtnLoading(btn, true, 'Deleting…');

  try {
    const res = await fetch(`/api/trips/${encodeURIComponent(tripId)}`, {
      method: 'DELETE',
      credentials: 'include'
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.message || 'Failed to delete trip.');
    }

    closeModal('modal-delete-confirm');
    showToast('Trip deleted successfully.', 'success');
    await loadDashboardData();

  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    setModalBtnLoading(btn, false, 'Delete Trip');
  }
}

/* ==========================================================================
   Logout
   ========================================================================== */
async function handleLogout() {
  try {
    await fetch('/api/auth/logout', {
      method: 'POST',
      credentials: 'include'
    });
  } catch (_) {
    // Redirect regardless
  } finally {
    window.location.href = '/login';
  }
}

/* ==========================================================================
   Modal Helpers
   ========================================================================== */
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (!modal) return;
  modal.classList.add('active');
  document.body.style.overflow = 'hidden';
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (!modal) return;
  modal.classList.remove('active');
  document.body.style.overflow = '';
}

function showFormError(alertBox, message) {
  if (!alertBox) return;
  alertBox.textContent = message;
  alertBox.className = 'form-message-box error';
  alertBox.style.display = 'block';
}

function setModalBtnLoading(btn, isLoading, text) {
  if (!btn) return;
  btn.disabled = isLoading;
  const span = btn.querySelector('span');
  if (span) span.textContent = text;
}

/* ==========================================================================
   Toast System
   ========================================================================== */
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.setAttribute('role', 'alert');

  const icon = type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ';
  toast.innerHTML = `<strong>${icon}</strong> <span>${escapeHtml(message)}</span>`;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

/* ==========================================================================
   Utility Helpers
   ========================================================================== */
function formatReadableDate(dateStr) {
  if (!dateStr) return '';
  try {
    const clean = String(dateStr).split('T')[0].split(' ')[0];
    const parts = clean.split('-');
    if (parts.length === 3) {
      const year = parseInt(parts[0], 10);
      const month = parseInt(parts[1], 10) - 1;
      const day = parseInt(parts[2], 10);
      const d = new Date(year, month, day);
      return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    }
    return clean;
  } catch (_) {
    return dateStr;
  }
}

function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

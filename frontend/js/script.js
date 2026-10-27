/**
 * Beyond Horizons — Global Homepage and Navigation Script
 */

document.addEventListener('DOMContentLoaded', () => {
  // Mobile Navigation Toggle
  const menuBtn = document.getElementById('mobile-menu-btn');
  const mainNav = document.getElementById('main-nav');

  if (menuBtn && mainNav) {
    menuBtn.addEventListener('click', () => {
      const isExpanded = menuBtn.getAttribute('aria-expanded') === 'true';
      menuBtn.setAttribute('aria-expanded', !isExpanded);
      mainNav.classList.toggle('active');
    });

    // Close navigation menu when clicking on any nav link
    mainNav.querySelectorAll('.nav-link').forEach(link => {
      link.addEventListener('click', () => {
        mainNav.classList.remove('active');
        menuBtn.setAttribute('aria-expanded', 'false');
      });
    });

    // Close when clicking outside
    document.addEventListener('click', (event) => {
      if (!mainNav.contains(event.target) && !menuBtn.contains(event.target) && mainNav.classList.contains('active')) {
        mainNav.classList.remove('active');
        menuBtn.setAttribute('aria-expanded', 'false');
      }
    });
  }

  // Check auth status to enhance navigation buttons
  checkUserSession();
});

async function checkUserSession() {
  try {
    const res = await fetch('/api/auth/me', { credentials: 'include' });
    if (!res.ok) return;
    const data = await res.json();
    if (data && data.authenticated && data.user) {
      // User is logged in: update header actions to link to Dashboard
      const navCtaBtn = document.getElementById('nav-cta-btn');
      if (navCtaBtn) {
        navCtaBtn.textContent = 'Dashboard →';
        navCtaBtn.href = '/dashboard';
      }
      const heroStartBtn = document.getElementById('hero-start-btn');
      if (heroStartBtn) {
        heroStartBtn.innerHTML = '<span>Go to Dashboard</span> <span>→</span>';
        heroStartBtn.href = '/dashboard';
      }
      const heroLoginBtn = document.getElementById('hero-login-btn');
      if (heroLoginBtn) {
        heroLoginBtn.style.display = 'none';
      }
      const navLoginLink = document.getElementById('nav-login-link');
      if (navLoginLink) {
        navLoginLink.textContent = 'Dashboard';
        navLoginLink.href = '/dashboard';
      }
    }
  } catch (_) {
    // Fail silently on home page if API is momentarily unreachable
  }
}

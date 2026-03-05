// Gestion du menu mobile
document.addEventListener('DOMContentLoaded', function() {
    const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
    const closeMenuButton = document.getElementById('close-menu');
    const mobileMenu = document.getElementById('mobile-menu');
    const menuOverlay = document.getElementById('menu-overlay');
    const bar1 = document.getElementById('bar1');
    const bar2 = document.getElementById('bar2');
    const bar3 = document.getElementById('bar3');

    if (!mobileMenuToggle || !mobileMenu) return;

    function openMenu() {
        mobileMenu.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
        if (bar1) {
            bar1.style.transform = 'translateY(4px) rotate(45deg)';
            bar2.style.opacity = '0';
            bar3.style.transform = 'translateY(-8px) rotate(-45deg)';
            bar3.style.width = '1.25rem';
        }
    }

    function closeMenu() {
        mobileMenu.classList.add('hidden');
        document.body.style.overflow = '';
        if (bar1) {
            bar1.style.transform = '';
            bar2.style.opacity = '1';
            bar3.style.transform = '';
            bar3.style.width = '';
        }
    }

    mobileMenuToggle.addEventListener('click', function() {
        if (mobileMenu.classList.contains('hidden')) {
            openMenu();
        } else {
            closeMenu();
        }
    });

    if (closeMenuButton) closeMenuButton.addEventListener('click', closeMenu);
    if (menuOverlay) menuOverlay.addEventListener('click', closeMenu);

    // Fermer le menu quand un lien est cliqué
    mobileMenu.querySelectorAll('a').forEach(function(link) {
        link.addEventListener('click', closeMenu);
    });
});

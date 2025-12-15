// Gestion du menu mobile
document.addEventListener('DOMContentLoaded', function() {
    const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
    const closeMenuButton = document.getElementById('close-menu');
    const mobileMenu = document.getElementById('mobile-menu');

    // Sécurité : ne rien faire si les éléments nécessaires ne sont pas dans le DOM
    if (!mobileMenuToggle || !closeMenuButton || !mobileMenu) {
        return;
    }

    const mobileMenuLinks = mobileMenu.querySelectorAll('a');

    // Ouvrir le menu mobile
    mobileMenuToggle.addEventListener('click', () => {
        mobileMenu.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    });

    // Fermer le menu mobile
    const closeMobileMenu = () => {
        mobileMenu.classList.add('hidden');
        document.body.style.overflow = '';
    };

    closeMenuButton.addEventListener('click', closeMobileMenu);

    // Fermer le menu quand un lien est cliqué
    mobileMenuLinks.forEach(link => {
        link.addEventListener('click', closeMobileMenu);
    });
});
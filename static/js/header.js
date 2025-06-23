// Gestion du menu mobile
document.addEventListener('DOMContentLoaded', function() {
    const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
    const closeMenuButton = document.getElementById('close-menu');
    const mobileMenu = document.getElementById('mobile-menu');
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

    // Gestion du thème
    const themeToggleDesktop = document.getElementById('theme-toggle-desktop');
    const themeToggleMobile = document.getElementById('theme-toggle-mobile');
    const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)');

    // Fonction pour définir le thème avec animation
    const setTheme = (isDark) => {
        // Ajouter une classe de transition pour l'animation
        document.documentElement.classList.add('theme-transition');
        
        if (isDark) {
            document.documentElement.classList.add('dark');
            localStorage.setItem('theme', 'dark');
        } else {
            document.documentElement.classList.remove('dark');
            localStorage.setItem('theme', 'light');
        }

        // Retirer la classe de transition après l'animation
        setTimeout(() => {
            document.documentElement.classList.remove('theme-transition');
        }, 500);
    };

    // Fonction pour vérifier et appliquer le thème initial
    const initializeTheme = () => {
        const savedTheme = localStorage.getItem('theme');
        
        if (savedTheme) {
            // Utiliser le thème sauvegardé
            setTheme(savedTheme === 'dark');
        } else {
            // Utiliser la préférence système
            setTheme(prefersDarkScheme.matches);
        }
    };

    // Gérer le changement de thème
    const handleThemeToggle = () => {
        const isDark = document.documentElement.classList.contains('dark');
        setTheme(!isDark);
    };

    // Écouter les changements de préférence système
    prefersDarkScheme.addEventListener('change', (e) => {
        // Ne changer que si l'utilisateur n'a pas défini de préférence
        if (!localStorage.getItem('theme')) {
            setTheme(e.matches);
        }
    });

    // Initialiser le thème
    initializeTheme();

    // Ajouter les écouteurs d'événements pour les boutons de thème
    themeToggleDesktop.addEventListener('click', handleThemeToggle);
    themeToggleMobile.addEventListener('click', handleThemeToggle);
}); 
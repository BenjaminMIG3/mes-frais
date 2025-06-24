document.addEventListener('DOMContentLoaded', function() {
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    const currentPath = window.location.pathname.replace(/\/$/, ''); // retire le slash final
    navLinks.forEach(link => {
        // On retire aussi le slash final du href pour comparer
        const linkPath = link.getAttribute('href').replace(/\/$/, '');
        
        if (linkPath && linkPath !== '#' && currentPath === linkPath) {
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');
        }
    });
});
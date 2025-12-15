document.addEventListener('DOMContentLoaded', function() {
    const carousels = document.querySelectorAll('[data-carousel]');
    carousels.forEach(carousel => {
        const items = carousel.querySelectorAll('[data-carousel-item]');
        const indicators = carousel.querySelectorAll('[data-carousel-slide-to]');
        let currentIndex = 0;

        const updateCarousel = (index) => {
            // Hide all items
            items.forEach((item, idx) => {
                item.classList.toggle('hidden', idx !== index);
            });

            // Update indicators
            indicators.forEach((indicator, idx) => {
                indicator.setAttribute('aria-current', idx === index ? 'true' : 'false');
                // Update indicator styling
                if (idx === index) {
                    indicator.classList.add('bg-brand-500', 'dark:bg-accent-500');
                    indicator.classList.remove('bg-brand-300', 'dark:bg-accent-700');
                } else {
                    indicator.classList.remove('bg-brand-500', 'dark:bg-accent-500');
                    indicator.classList.add('bg-brand-300', 'dark:bg-accent-700');
                }
            });
        };

        const nextButton = carousel.querySelector('[data-carousel-next]');
        const prevButton = carousel.querySelector('[data-carousel-prev]');

        if (nextButton) {
            nextButton.addEventListener('click', () => {
                currentIndex = (currentIndex + 1) % items.length;
                updateCarousel(currentIndex);
            });
        }

        if (prevButton) {
            prevButton.addEventListener('click', () => {
                currentIndex = (currentIndex - 1 + items.length) % items.length;
                updateCarousel(currentIndex);
            });
        }

        // Add click handlers for indicators
        indicators.forEach((indicator, index) => {
            indicator.addEventListener('click', () => {
                currentIndex = index;
                updateCarousel(currentIndex);
            });
        });

        // Initialize the carousel
        if (items.length > 0) {
            updateCarousel(currentIndex);
        }
    });
});


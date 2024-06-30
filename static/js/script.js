document.addEventListener('DOMContentLoaded', () => {
  const themeToggle = document.getElementById('theme-toggle');

  if (!themeToggle) {
    console.error('Element with id "theme-toggle" not found.');
    return;
  }

  themeToggle.addEventListener('click', () => {
    if (localStorage.theme === 'dark') {
      localStorage.theme = 'light';
      document.documentElement.classList.remove('dark');
    } else {
      localStorage.theme = 'dark';
      document.documentElement.classList.add('dark');
    }
  });

  // On page load or when changing themes, best to add inline in `head` to avoid FOUC
  if (localStorage.theme === 'dark' || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
    document.documentElement.classList.add('dark');
  } else {
    document.documentElement.classList.remove('dark');
  }
});

document.addEventListener('DOMContentLoaded', function() {
    const carousels = document.querySelectorAll('[data-carousel]');
    carousels.forEach(carousel => {
        const items = carousel.querySelectorAll('[data-carousel-item]');
        let currentIndex = 0;

        const updateCarousel = (index) => {
            items.forEach((item, idx) => {
                item.classList.toggle('hidden', idx !== index);
            });

            // Set the current indicator button
            const indicators = carousel.querySelectorAll('[data-carousel-slide-to]');
            indicators.forEach(indicator => {
                indicator.setAttribute('aria-current', 'false');
            });
            indicators[index].setAttribute('aria-current', 'true');
        };

        const nextButton = carousel.querySelector('[data-carousel-next]');
        const prevButton = carousel.querySelector('[data-carousel-prev]');

        nextButton.addEventListener('click', () => {
            currentIndex = (currentIndex + 1) % items.length;
            updateCarousel(currentIndex);
        });

        prevButton.addEventListener('click', () => {
            currentIndex = (currentIndex - 1 + items.length) % items.length;
            updateCarousel(currentIndex);
        });

        // Initialize the carousel
        updateCarousel(currentIndex);
    });
});
const updateCarousel = (index) => {
  items.forEach((item, idx) => {
    if (idx === index) {
      item.classList.add('active');
      item.classList.remove('hidden');
    } else {
      item.classList.remove('active');
      item.classList.add('hidden');
    }
  });
};


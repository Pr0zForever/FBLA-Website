let lastScrollY = window.scrollY;

window.addEventListener('scroll', () => {
  const header = document.querySelector('.header');

  if (window.scrollY > lastScrollY) {
    // Scrolling down - hide the header
    header.classList.add('hidden');
  } else {
    // Scrolling up - show the header
    header.classList.remove('hidden');
  }

  lastScrollY = window.scrollY;
});

const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
        if(entry.isIntersecting){
            entry.target.classList.add('show');
        } else{
            entry.target.classList.remove('show');
        }
    })
})

const hiddenElements = document.querySelectorAll(".hero, .features, .cta");

hiddenElements.forEach((el) => observer.observe(el));
const svg = document.getElementById('dna-svg');
const dnaTimeline = anime.timeline({ autoplay: false, easing: 'linear' });

function createStrand(numRungs, className) {
    const rungs = [];
    for (let i = 0; i < numRungs; i++) {
        const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
        line.classList.add('dna-rung', className);
        svg.appendChild(line);
        rungs.push(line);
    }
    return rungs;
}

const cyanStrand = createStrand(45, 'cyan');
const purpleStrand = createStrand(35, 'purple');
const goldStrand = createStrand(30, 'gold');

// --- INITIAL STATE (HELIXES) ---
// Cyan (Main - Middle Speed)
dnaTimeline.add({
    targets: cyanStrand,
    x1: (el, i) => 500 + Math.sin(i * 0.4) * 120,
    x2: (el, i) => 500 - Math.sin(i * 0.4) * 120,
    y1: (el, i) => i * 22,
    y2: (el, i) => i * 22,
    opacity: [0, 0.8],
    duration: 1000
}, 0);

// Purple (Background - Slower Speed)
dnaTimeline.add({
    targets: purpleStrand,
    x1: (el, i) => 250 + Math.sin(i * 0.6) * 70,
    x2: (el, i) => 250 - Math.sin(i * 0.6) * 70,
    y1: (el, i) => i * 30,
    y2: (el, i) => i * 30,
    opacity: [0, 0.5],
    duration: 1000
}, 0);

// Gold (Foreground - Faster Speed)
dnaTimeline.add({
    targets: goldStrand,
    x1: (el, i) => 750 + Math.sin(i * 0.8) * 50,
    x2: (el, i) => 750 - Math.sin(i * 0.8) * 50,
    y1: (el, i) => i * 35,
    y2: (el, i) => i * 35,
    opacity: [0, 0.6],
    duration: 1000
}, 0);

// --- UNWINDING STATE ---
dnaTimeline.add({
    targets: '.dna-rung',
    x1: 450,
    x2: 550,
    duration: 1000,
    delay: anime.stagger(2)
}, 500);

let targetProgress = 0;
let currentProgress = 0;

window.addEventListener('scroll', () => {
    const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
    targetProgress = window.scrollY / maxScroll;
});

// Animation loop
function animateScroll() {
    // Smooth interpolation
    currentProgress += (targetProgress - currentProgress) * 0.08;

    dnaTimeline.seek(currentProgress * dnaTimeline.duration);

    // Parallax without re-triggering anime()
    purpleStrand.forEach(el => {
        el.setAttribute("transform", `translate(0, ${currentProgress * 150})`);
    });

    goldStrand.forEach(el => {
        el.setAttribute("transform", `translate(0, ${currentProgress * -200})`);
    });

    svg.style.transform = `
        scale(${1 + currentProgress * 0.2})
    `;

    requestAnimationFrame(animateScroll);
}

animateScroll();

// Intersection Observer for content
const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) entry.target.classList.add('visible');
    });
}, { threshold: 0.3 });

document.querySelectorAll('.panel').forEach(p => observer.observe(p));

// 1. Handle Navbar Scroll Effect
window.addEventListener('scroll', () => {
    const nav = document.querySelector('.navbar');
    if (window.scrollY > 50) {
        nav.classList.add('scrolled');
    } else {
        nav.classList.remove('scrolled');
    }
});

// 2. Enhanced Intersection Observer for Nav Highlighting
const navLinks = document.querySelectorAll('.nav-right a');
const navObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const id = entry.target.getAttribute('id');
            navLinks.forEach(link => {
                link.classList.remove('active');
                if (link.getAttribute('href') === `#${id}`) {
                    link.classList.add('active');
                }
            });
        }
    });
}, { threshold: 0.6 });

document.querySelectorAll('.panel').forEach(p => navObserver.observe(p));
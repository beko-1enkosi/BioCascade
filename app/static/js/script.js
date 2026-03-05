// Register the ScrollTrigger plugin
gsap.registerPlugin(ScrollTrigger);

/**
 * 1. DNA SVG GENERATION
 * Creates the three strands (Cyan, Purple, Gold)
 */
const svg = document.getElementById('dna-svg');

const createStrand = (numRungs, className) => {
    const rungs = [];

    for (let i = 0; i < numRungs; i++) {
        const line = document.createElementNS("http://www.w3.org/2000/svg", "line");

        line.classList.add("dna-rung", className);

        // Give initial attributes so lines exist before animation
        line.setAttribute("x1", 500);
        line.setAttribute("x2", 500);
        line.setAttribute("y1", i * 20);
        line.setAttribute("y2", i * 20);

        svg.appendChild(line);
        rungs.push(line);
    }

    return rungs;
};

const cyanStrand = createStrand(45, "cyan");
const purpleStrand = createStrand(35, "purple");
const goldStrand = createStrand(30, "gold");


/**
 * 2. HERO ENTRANCE ANIMATION
 */
window.addEventListener("load", () => {

    const introTl = gsap.timeline({ defaults: { ease: "expo.out" } });

    introTl
        .to(".main-title", {
            y: 0,
            duration: 1.8,
            delay: 0.2
        })

        .to(".hero-description, .hackathon-tag", {
            opacity: 1,
            y: 0,
            duration: 1,
            stagger: 0.2
        }, "-=1.2")

        .to(".hero-actions, .scroll-indicator, .navbar", {
            opacity: 1,
            duration: 1
        }, "-=0.8");
});


/**
 * 3. SCROLL-LINKED DNA ANIMATION
 */
const dnaTl = gsap.timeline({

    scrollTrigger: {
        trigger: document.body,
        start: "top top",
        end: "bottom bottom",
        scrub: 1.5
    }

});


/* ===========================
   CYAN STRAND
   =========================== */

dnaTl.fromTo(
    cyanStrand,
    {
        attr: {
            x1: (i) => 500 + Math.sin(i * 0.4) * 120,
            x2: (i) => 500 - Math.sin(i * 0.4) * 120,
            y1: (i) => i * 22,
            y2: (i) => i * 22
        },
        opacity: 0
    },
    {
        attr: {
            x1: 450,
            x2: 550
        },
        opacity: 0.8,
        duration: 1
    },
    0
);


/* ===========================
   PURPLE STRAND
   =========================== */

dnaTl.fromTo(
    purpleStrand,
    {
        attr: {
            x1: (i) => 250 + Math.sin(i * 0.6) * 70,
            x2: (i) => 250 - Math.sin(i * 0.6) * 70,
            y1: (i) => i * 30,
            y2: (i) => i * 30
        },
        opacity: 0
    },
    {
        attr: {
            x1: 480,
            x2: 520
        },
        opacity: 0.4,
        duration: 1
    },
    0
);


/* ===========================
   GOLD STRAND
   =========================== */

dnaTl.fromTo(
    goldStrand,
    {
        attr: {
            x1: (i) => 750 + Math.sin(i * 0.8) * 50,
            x2: (i) => 750 - Math.sin(i * 0.8) * 50,
            y1: (i) => i * 35,
            y2: (i) => i * 35
        },
        opacity: 0
    },
    {
        attr: {
            x1: 490,
            x2: 510
        },
        opacity: 0.5,
        duration: 1
    },
    0
);


/**
 * 4. MOUSE PARALLAX
 */

const moveTitleX = gsap.quickTo(".main-title", "x", { duration: 1, ease: "power2.out" });
const moveTitleY = gsap.quickTo(".main-title", "y", { duration: 1, ease: "power2.out" });

const moveDNAx = gsap.quickTo("#dna-svg", "x", { duration: 2 });
const moveDNAy = gsap.quickTo("#dna-svg", "y", { duration: 2 });

document.addEventListener("mousemove", (e) => {

    const xMove = (e.clientX / window.innerWidth - 0.5) * 30;
    const yMove = (e.clientY / window.innerHeight - 0.5) * 30;

    moveTitleX(xMove);
    moveTitleY(yMove);

    moveDNAx(-xMove * 0.5);
    moveDNAy(-yMove * 0.5);

});


/**
 * 5. NAVBAR SCROLL EFFECT
 */

window.addEventListener("scroll", () => {

    const nav = document.querySelector(".navbar");

    if (window.scrollY > 80) {
        nav.classList.add("scrolled");
    } else {
        nav.classList.remove("scrolled");
    }

});


/**
 * 6. NAV LINK ACTIVE STATE
 */

const navLinks = document.querySelectorAll(".nav-center a");

const observer = new IntersectionObserver((entries) => {

    entries.forEach(entry => {

        if (entry.isIntersecting) {

            const id = entry.target.getAttribute("id");

            navLinks.forEach(link => {

                link.classList.remove("active");

                if (link.getAttribute("href") === `#${id}`) {
                    link.classList.add("active");
                }

            });

            entry.target.classList.add("visible");

        }

    });

}, { threshold: 0.4 });

document.querySelectorAll(".panel").forEach(p => observer.observe(p));


/**
 * 7. SMOOTH NAVIGATION SCROLL
 */

document.querySelectorAll(".nav-center a").forEach(link => {

    link.addEventListener("click", e => {

        e.preventDefault();

        const target = document.querySelector(link.getAttribute("href"));

        gsap.to(window, {
            duration: 1.2,
            scrollTo: target,
            ease: "power2.out"
        });

    });

});


/**
 * 8. SLOW DNA ROTATION
 */

gsap.to("#dna-svg", {

    rotate: 360,
    duration: 120,
    repeat: -1,
    ease: "none",
    transformOrigin: "center center"

});

// /**
//  * ABOUT SECTION CASCADE ANIMATION
//  */

// gsap.from(".cascade-node", {

//     scrollTrigger: {
//         trigger: "#about",
//         start: "top 70%"
//     },

//     opacity: 0,
//     y: 40,
//     stagger: 0.25,
//     duration: 1.2,
//     ease: "power3.out"
    
// });


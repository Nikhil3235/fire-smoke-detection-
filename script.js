/**
 * ============================================================
 *  Fire & Smoke Detection AI — Premium Interactive Script
 * ============================================================
 *  Vanilla ES6+ · IntersectionObserver · requestAnimationFrame
 *  No external dependencies
 * ============================================================
 */

document.addEventListener('DOMContentLoaded', () => {

  /* ──────────────────────────────────────────────
   *  1.  FIRE-EMBER PARTICLE SYSTEM
   * ────────────────────────────────────────────── */
  const initParticles = () => {
    const PARTICLE_COUNT = 50;
    const COLORS = ['#ff6b35', '#ff9f1c', '#e63946', '#ffbe0b'];

    // Create & append container
    const container = document.createElement('div');
    container.classList.add('particle-container');
    Object.assign(container.style, {
      position: 'fixed',
      inset: '0',
      pointerEvents: 'none',
      zIndex: '0',
      overflow: 'hidden',
    });
    document.body.appendChild(container);

    const createParticle = () => {
      const el = document.createElement('span');
      const size = Math.random() * 4 + 2;                       // 2–6 px
      const x    = Math.random() * 100;                          // 0–100 vw
      const dur  = Math.random() * 25 + 15;                     // 15–40 s
      const delay = Math.random() * dur * -1;                   // negative = staggered start
      const opacity = (Math.random() * 0.5 + 0.1).toFixed(2);  // 0.1–0.6
      const color = COLORS[Math.floor(Math.random() * COLORS.length)];

      Object.assign(el.style, {
        position: 'absolute',
        bottom: '-10px',
        left: `${x}vw`,
        width: `${size}px`,
        height: `${size}px`,
        borderRadius: '50%',
        background: color,
        boxShadow: `0 0 ${size * 2}px ${color}`,
        opacity,
        animation: `ember-float ${dur}s linear ${delay}s infinite`,
        willChange: 'transform, opacity',
      });

      container.appendChild(el);
    };

    for (let i = 0; i < PARTICLE_COUNT; i++) createParticle();
  };


  /* ──────────────────────────────────────────────
   *  2.  NAVBAR SCROLL EFFECT
   * ────────────────────────────────────────────── */
  const initNavbar = () => {
    const navbar = document.querySelector('.navbar');
    if (!navbar) return;

    const SCROLL_THRESHOLD = 50;

    const onScroll = () => {
      navbar.classList.toggle('scrolled', window.scrollY > SCROLL_THRESHOLD);
    };

    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll(); // set initial state
  };


  /* ──────────────────────────────────────────────
   *  3.  SMOOTH SCROLL FOR NAV LINKS
   * ────────────────────────────────────────────── */
  const initSmoothScroll = () => {
    const navLinks = document.querySelectorAll('a[href^="#"]');
    const navbar   = document.querySelector('.navbar');
    const navMenu  = document.querySelector('.nav-links');
    const toggle   = document.querySelector('.mobile-toggle');

    navLinks.forEach(link => {
      link.addEventListener('click', (e) => {
        const targetId = link.getAttribute('href');
        if (targetId === '#') return;

        const target = document.querySelector(targetId);
        if (!target) return;

        e.preventDefault();

        const navHeight = navbar ? navbar.offsetHeight : 0;
        const top = target.getBoundingClientRect().top + window.scrollY - navHeight;

        window.scrollTo({ top, behavior: 'smooth' });

        // Close mobile menu if open
        if (navMenu) navMenu.classList.remove('active');
        if (toggle)  toggle.classList.remove('active');
      });
    });
  };


  /* ──────────────────────────────────────────────
   *  4.  MOBILE MENU TOGGLE
   * ────────────────────────────────────────────── */
  const initMobileMenu = () => {
    const toggle  = document.querySelector('.mobile-toggle');
    const navMenu = document.querySelector('.nav-links');
    if (!toggle || !navMenu) return;

    toggle.addEventListener('click', () => {
      toggle.classList.toggle('active');
      navMenu.classList.toggle('active');
    });

    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
      if (!toggle.contains(e.target) && !navMenu.contains(e.target)) {
        toggle.classList.remove('active');
        navMenu.classList.remove('active');
      }
    });
  };


  /* ──────────────────────────────────────────────
   *  5.  SCROLL-REVEAL (IntersectionObserver)
   * ────────────────────────────────────────────── */
  const initScrollReveal = () => {
    const reveals = document.querySelectorAll('.reveal');
    if (!reveals.length) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          if (!entry.isIntersecting) return;

          const el = entry.target;
          el.classList.add('active');

          // Stagger children that have .reveal-child
          const children = el.querySelectorAll('.reveal-child');
          children.forEach((child, i) => {
            child.style.transitionDelay = `${i * 100}ms`;
            child.classList.add('active');
          });

          observer.unobserve(el); // animate once
        });
      },
      { threshold: 0.1, rootMargin: '0px 0px -50px 0px' }
    );

    reveals.forEach(el => observer.observe(el));
  };


  /* ──────────────────────────────────────────────
   *  6.  ANIMATED NUMBER COUNTERS
   * ────────────────────────────────────────────── */
  const initCounters = () => {
    const counters = document.querySelectorAll('.counter[data-target]');
    if (!counters.length) return;

    // Ease-out exponential curve
    const easeOutExpo = (t) => (t === 1 ? 1 : 1 - Math.pow(2, -10 * t));

    const animateCounter = (el) => {
      if (el.dataset.animated) return;
      el.dataset.animated = 'true';

      const target   = parseFloat(el.dataset.target);
      const decimals = parseInt(el.dataset.decimals, 10) || 0;
      const suffix   = el.dataset.suffix || '';
      const duration = 2500; // ms
      let start = null;

      const step = (timestamp) => {
        if (!start) start = timestamp;
        const progress = Math.min((timestamp - start) / duration, 1);
        const eased    = easeOutExpo(progress);
        const current  = eased * target;

        el.textContent = current.toFixed(decimals) + suffix + (suffix !== '%' ? '+' : '');

        if (progress < 1) {
          requestAnimationFrame(step);
        } else {
          // Final value — ensure precision
          el.textContent = target.toFixed(decimals) + suffix + (suffix !== '%' ? '+' : '');
        }
      };

      requestAnimationFrame(step);
    };

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            animateCounter(entry.target);
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.3 }
    );

    counters.forEach(el => observer.observe(el));
  };


  /* ──────────────────────────────────────────────
   *  7.  VIDEO SECTION INTERACTION
   * ────────────────────────────────────────────── */
  const initVideoPlayer = () => {
    const overlay  = document.querySelector('.video-overlay');
    const playBtn  = document.querySelector('.play-button');
    const wrapper  = document.querySelector('.video-wrapper');
    const video    = wrapper ? wrapper.querySelector('video') : null;

    if (!overlay || !playBtn || !video) return;

    const showOverlay = () => {
      overlay.style.opacity = '1';
      overlay.style.pointerEvents = 'auto';
      wrapper.classList.remove('playing');
    };

    const hideOverlay = () => {
      overlay.style.opacity = '0';
      overlay.style.pointerEvents = 'none';
      wrapper.classList.add('playing');
    };

    playBtn.addEventListener('click', () => {
      hideOverlay();
      video.play();
    });

    video.addEventListener('pause', showOverlay);
    video.addEventListener('ended', () => {
      showOverlay();
      video.currentTime = 0;
    });
  };


  /* ──────────────────────────────────────────────
   *  8.  TILT / PARALLAX EFFECT ON CARDS
   * ────────────────────────────────────────────── */
  const initTiltEffect = () => {
    const cards = document.querySelectorAll('.stat-card, .tech-card');
    if (!cards.length) return;

    const MAX_ROTATION = 5; // degrees

    cards.forEach(card => {
      card.style.transition = 'transform 0.35s cubic-bezier(.25,.46,.45,.94)';
      card.style.willChange = 'transform';

      card.addEventListener('mousemove', (e) => {
        const rect = card.getBoundingClientRect();
        const cx   = rect.left + rect.width / 2;
        const cy   = rect.top  + rect.height / 2;

        // -1 → 1 normalised offset from center
        const dx = (e.clientX - cx) / (rect.width / 2);
        const dy = (e.clientY - cy) / (rect.height / 2);

        const rotateY =  dx * MAX_ROTATION;
        const rotateX = -dy * MAX_ROTATION;

        card.style.transform =
          `perspective(1000px) rotateX(${rotateX.toFixed(2)}deg) rotateY(${rotateY.toFixed(2)}deg) scale3d(1.02,1.02,1.02)`;
      });

      card.addEventListener('mouseleave', () => {
        card.style.transform =
          'perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1,1,1)';
      });
    });
  };


  /* ──────────────────────────────────────────────
   *  9.  ACTIVE NAV-LINK HIGHLIGHTING
   * ────────────────────────────────────────────── */
  const initActiveNav = () => {
    const sections = document.querySelectorAll('section[id]');
    const navLinks = document.querySelectorAll('.nav-links a[href^="#"]');
    if (!sections.length || !navLinks.length) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          if (!entry.isIntersecting) return;

          const id = entry.target.getAttribute('id');

          navLinks.forEach(link => {
            link.classList.toggle(
              'active',
              link.getAttribute('href') === `#${id}`
            );
          });
        });
      },
      {
        threshold: 0.25,
        rootMargin: '-80px 0px -50% 0px', // bias toward top of viewport
      }
    );

    sections.forEach(section => observer.observe(section));
  };


  /* ──────────────────────────────────────────────
   *  10.  STAGGERED GRID-ITEM ANIMATIONS
   * ────────────────────────────────────────────── */
  const initStaggeredGrids = () => {
    const grids = document.querySelectorAll(
      '.stats-grid, .tech-grid, .features-grid'
    );
    if (!grids.length) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          if (!entry.isIntersecting) return;

          const cards = entry.target.querySelectorAll(
            '.stat-card, .tech-card, .feature-card'
          );
          cards.forEach((card, i) => {
            card.style.transitionDelay = `${i * 100}ms`;
            card.classList.add('revealed');
          });

          observer.unobserve(entry.target);
        });
      },
      { threshold: 0.1 }
    );

    grids.forEach(grid => observer.observe(grid));
  };


  /* ──────────────────────────────────────────────
   *  11.  PAGE-LOAD ORCHESTRATION
   * ────────────────────────────────────────────── */
  const initPageLoad = () => {
    // Small delay so initial CSS transitions can trigger
    requestAnimationFrame(() => {
      setTimeout(() => {
        document.body.classList.add('loaded');

        // Sequentially reveal hero elements
        const heroElements = document.querySelectorAll(
          '.hero-badge, .hero h1, .hero p, .hero-buttons, .hero-stats'
        );

        heroElements.forEach((el, i) => {
          setTimeout(() => {
            el.classList.add('animate-in');
          }, i * 150); // 150ms stagger between hero children
        });
      }, 100);
    });
  };


  /* ──────────────────────────────────────────────
   *  12.  CUSTOM CURSOR GLOW (bonus premium feel)
   * ────────────────────────────────────────────── */
  const initCursorGlow = () => {
    // Only on non-touch devices
    if ('ontouchstart' in window) return;

    // 1. Soft Background Radial Glow
    const glow = document.createElement('div');
    glow.classList.add('cursor-glow');
    Object.assign(glow.style, {
      position: 'fixed',
      width: '320px',
      height: '320px',
      borderRadius: '50%',
      background: 'radial-gradient(circle, rgba(255,107,53,0.07) 0%, transparent 70%)',
      pointerEvents: 'none',
      zIndex: '9999',
      transform: 'translate(-50%, -50%)',
      transition: 'opacity 0.4s ease',
      opacity: '0',
      willChange: 'left, top',
    });
    document.body.appendChild(glow);

    // 2. Flame Particle Canvas Overlay
    const canvas = document.createElement('canvas');
    canvas.id = 'flameCursorCanvas';
    Object.assign(canvas.style, {
      position: 'fixed',
      top: '0',
      left: '0',
      width: '100vw',
      height: '100vh',
      pointerEvents: 'none',
      zIndex: '999999'
    });
    document.body.appendChild(canvas);

    const ctx = canvas.getContext('2d');
    let width = canvas.width = window.innerWidth;
    let height = canvas.height = window.innerHeight;

    window.addEventListener('resize', () => {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    }, { passive: true });

    const particles = [];
    let cursorX = 0;
    let cursorY = 0;
    let glowX   = 0;
    let glowY   = 0;
    let lastMouseTime = 0;

    document.addEventListener('mousemove', (e) => {
      cursorX = e.clientX;
      cursorY = e.clientY;
      glow.style.opacity = '1';

      // Limit particle generation rate slightly for performance
      const now = performance.now();
      if (now - lastMouseTime > 15) {
        lastMouseTime = now;
        // Spawn 2-3 flame particles per mouse move
        for (let i = 0; i < 2; i++) {
          particles.push({
            x: cursorX + (Math.random() - 0.5) * 6,
            y: cursorY + (Math.random() - 0.5) * 6,
            vx: (Math.random() - 0.5) * 1.0,
            vy: -Math.random() * 1.8 - 0.6, // Float upwards
            alpha: 1.0,
            decay: Math.random() * 0.025 + 0.015,
            size: Math.random() * 6 + 3,
            color: Math.random() > 0.45 ? 'rgba(255, 78, 0, ' : 'rgba(255, 165, 0, ' // Fire theme orange/yellow
          });
        }
      }
    }, { passive: true });

    document.addEventListener('mouseleave', () => {
      glow.style.opacity = '0';
    });

    // Animate loop for glow positioning and flame particles drawing
    const updateCursorGlow = () => {
      // 1. Update radial glow position smoothly
      glowX += (cursorX - glowX) * 0.12;
      glowY += (cursorY - glowY) * 0.12;
      glow.style.left = `${glowX}px`;
      glow.style.top  = `${glowY}px`;

      // 2. Draw flame particles
      ctx.clearRect(0, 0, width, height);
      for (let i = particles.length - 1; i >= 0; i--) {
        const p = particles[i];
        p.x += p.vx;
        p.y += p.vy;
        p.alpha -= p.decay;
        p.size *= 0.96; // Shrink particle

        if (p.alpha <= 0 || p.size < 0.5) {
          particles.splice(i, 1);
          continue;
        }

        // Beautiful glowing flame drawing
        ctx.save();
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = p.color + p.alpha * 0.75 + ')'; // semi-transparent glow, not too dark
        ctx.shadowColor = p.color + '0.4)';
        ctx.shadowBlur = p.size * 1.5;
        ctx.fill();
        ctx.restore();
      }

      requestAnimationFrame(updateCursorGlow);
    };
    requestAnimationFrame(updateCursorGlow);
  };


  /* ──────────────────────────────────────────────
   *  13.  PARALLAX HERO BACKGROUND
   * ────────────────────────────────────────────── */
  const initHeroParallax = () => {
    const hero = document.querySelector('.hero');
    if (!hero) return;

    window.addEventListener('scroll', () => {
      const scrolled = window.scrollY;
      if (scrolled < window.innerHeight) {
        hero.style.setProperty('--parallax-y', `${scrolled * 0.35}px`);
      }
    }, { passive: true });
  };


  /* ──────────────────────────────────────────────
   *  14.  THROTTLE UTILITY (internal)
   * ────────────────────────────────────────────── */
  // Used internally by resize-sensitive modules if needed
  const throttle = (fn, wait = 100) => {
    let lastTime = 0;
    return (...args) => {
      const now = performance.now();
      if (now - lastTime >= wait) {
        lastTime = now;
        fn(...args);
      }
    };
  };


  /* ──────────────────────────────────────────────
   *  15.  PERFORMANCE BAR ANIMATIONS
   * ────────────────────────────────────────────── */
  const initPerformanceBars = () => {
    const perfSection = document.querySelector('.performance-section');
    if (!perfSection) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          if (!entry.isIntersecting) return;

          const fills = entry.target.querySelectorAll('.perf-fill');
          fills.forEach((fill, i) => {
            const targetWidth = fill.dataset.width || 0;
            setTimeout(() => {
              fill.style.width = `${targetWidth}%`;
              fill.classList.add('animated');
            }, i * 200); // stagger each bar by 200ms
          });

          observer.unobserve(entry.target);
        });
      },
      { threshold: 0.2 }
    );

    observer.observe(perfSection);
  };

  const checkCameraAvailability = async () => {
    const statusEl = document.createElement('div');
    statusEl.id = 'cameraStatusBanner';
    statusEl.style.fontSize = '0.75rem';
    statusEl.style.marginTop = '0.5rem';
    statusEl.style.fontWeight = '600';
    statusEl.style.display = 'inline-block';
    statusEl.style.padding = '4px 10px';
    statusEl.style.borderRadius = '6px';
    statusEl.style.transition = 'all 0.3s ease';

    const sourceSelect = document.getElementById('sourceSelect');
    if (!sourceSelect) return;
    const selectContainer = sourceSelect.parentNode;

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        statusEl.textContent = '📷 Camera: ❌ Blocked/Unsupported (Use Chrome/Firefox over HTTPS)';
        statusEl.style.background = 'rgba(239, 68, 68, 0.15)';
        statusEl.style.color = '#ef4444';
        statusEl.style.border = '1px solid rgba(239, 68, 68, 0.2)';
    } else {
        try {
            if (navigator.permissions && navigator.permissions.query) {
                const permissionStatus = await navigator.permissions.query({ name: 'camera' });
                const updateStatus = (state) => {
                    if (state === 'granted') {
                        statusEl.textContent = '📷 Camera: ✅ Ready (Permission Granted)';
                        statusEl.style.background = 'rgba(16, 185, 129, 0.15)';
                        statusEl.style.color = '#10b981';
                        statusEl.style.border = '1px solid rgba(16, 185, 129, 0.2)';
                    } else if (state === 'prompt') {
                        statusEl.textContent = '📷 Camera: ⚡ Ready (Will Ask for Permission)';
                        statusEl.style.background = 'rgba(59, 130, 246, 0.15)';
                        statusEl.style.color = '#3b82f6';
                        statusEl.style.border = '1px solid rgba(59, 130, 246, 0.2)';
                    } else {
                        statusEl.textContent = '📷 Camera: ⚠ Blocked (Please click lock icon in URL bar to Allow)';
                        statusEl.style.background = 'rgba(245, 158, 11, 0.15)';
                        statusEl.style.color = '#f59e0b';
                        statusEl.style.border = '1px solid rgba(245, 158, 11, 0.2)';
                    }
                };
                updateStatus(permissionStatus.state);
                permissionStatus.onchange = () => {
                    updateStatus(permissionStatus.state);
                };
            } else {
                statusEl.textContent = '📷 Camera: ✅ Ready';
                statusEl.style.background = 'rgba(16, 185, 129, 0.15)';
                statusEl.style.color = '#10b981';
                statusEl.style.border = '1px solid rgba(16, 185, 129, 0.2)';
            }
        } catch (e) {
            statusEl.textContent = '📷 Camera: ✅ Ready';
            statusEl.style.background = 'rgba(16, 185, 129, 0.15)';
            statusEl.style.color = '#10b981';
            statusEl.style.border = '1px solid rgba(16, 185, 129, 0.2)';
        }
    }
    
    const existing = document.getElementById('cameraStatusBanner');
    if (existing) existing.remove();
    selectContainer.appendChild(statusEl);
  };


  /* ═══════════════════════════════════════════════
   *  BOOTSTRAP — wire everything up
   * ═══════════════════════════════════════════════ */
  initParticles();
  initNavbar();
  initSmoothScroll();
  initMobileMenu();
  initScrollReveal();
  initCounters();
  initVideoPlayer();
  initTiltEffect();
  initActiveNav();
  initStaggeredGrids();
  initPageLoad();
  initCursorGlow();
  initHeroParallax();
  initPerformanceBars();
  checkCameraAvailability();

  /* ──────────────────────────────────────────────
   *  16.  LIVE AI DASHBOARD LOGIC
   * ────────────────────────────────────────────── */
  if (!localStorage.getItem('fire_session_id')) {
      localStorage.setItem('fire_session_id', 'sess_' + Math.random().toString(36).substr(2, 9) + Date.now().toString(36));
  }
  window.sessionId = localStorage.getItem('fire_session_id');

  let detecting = false;
  let statsInterval = null;
  let audioCtx = null;
  let sirenInterval = null;
  let mediaRecorder = null;
  let recordedChunks = [];
  
  let webcamStream = null;
  let webcamFrameId = null;
  const hiddenCanvas = document.createElement('canvas');
  const hiddenCtx = hiddenCanvas.getContext('2d');
  
  // Setup Chart.js
  const chartCanvas = document.getElementById('confidenceChart');
  let confidenceChart = null;
  if (chartCanvas) {
    const ctx = chartCanvas.getContext('2d');
    confidenceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: Array(10).fill(''),
            datasets: [
                {
                    label: 'Fire',
                    borderColor: '#ff4d00',
                    backgroundColor: 'rgba(255, 77, 0, 0.1)',
                    data: Array(10).fill(0),
                    borderWidth: 2,
                    tension: 0.3
                },
                {
                    label: 'Smoke',
                    borderColor: '#a0a0b0',
                    backgroundColor: 'rgba(160, 160, 176, 0.1)',
                    data: Array(10).fill(0),
                    borderWidth: 2,
                    tension: 0.3
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: { min: 0, max: 100, grid: { color: 'rgba(255,255,255,0.02)' }, ticks: { color: '#7e7e8f' } },
                x: { grid: { display: false } }
            }
        }
    });
  }

  // Web Audio API Siren
  window.playSiren = () => {
      if (!document.getElementById('alarmToggle').checked) return;
      if (sirenInterval) return;

      if (!audioCtx) {
          audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      }

      let osc = audioCtx.createOscillator();
      let gain = audioCtx.createGain();
      osc.connect(gain);
      gain.connect(audioCtx.destination);

      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(440, audioCtx.currentTime);
      gain.gain.setValueAtTime(0.15, audioCtx.currentTime);

      osc.start();

      sirenInterval = setInterval(() => {
          let time = audioCtx.currentTime;
          osc.frequency.linearRampToValueAtTime(880, time + 0.4);
          osc.frequency.linearRampToValueAtTime(440, time + 0.8);
      }, 800);

      window.activeOsc = osc;
      window.activeGain = gain;
  };

  window.stopSiren = () => {
      if (sirenInterval) {
          clearInterval(sirenInterval);
          sirenInterval = null;
      }
      if (window.activeOsc) {
          try { window.activeOsc.stop(); } catch(e) {}
          window.activeOsc = null;
      }
  };

  window.addLog = (message, isAlert = false) => {
      const logBox = document.getElementById('logBox');
      if (!logBox) return;
      const timestamp = new Date().toLocaleTimeString();
      const logLine = document.createElement('div');
      logLine.className = 'log-line';
      logLine.style.marginBottom = '0.4rem';
      logLine.style.display = 'flex';
      logLine.style.gap = '0.8rem';
      logLine.innerHTML = `
          <span class="log-time" style="color: var(--accent-teal);">[${timestamp}]</span>
          <span class="log-text" style="color: ${isAlert ? '#ff3344' : 'var(--text-secondary)'}; font-weight: ${isAlert ? 'bold' : 'normal'};">${message}</span>
      `;
      logBox.appendChild(logLine);
      logBox.scrollTop = logBox.scrollHeight;
  };

  window.saveNotificationConfig = () => {
      const payload = {
          sms: {
              enabled: document.getElementById('smsEnable').checked,
              to_number: document.getElementById('smsTo').value,
              account_sid: document.getElementById('smsSid').value,
              auth_token: document.getElementById('smsToken').value,
              from_number: document.getElementById('smsFrom').value
          }
      };

      fetch('/api/config', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
      }).then(r => r.json()).then(data => {
          if (data.success) {
              window.addLog("SMS notification configuration updated.");
          }
      });
  };

  window.startStream = async () => {
      const source = document.getElementById('sourceSelect').value;
      const conf = document.getElementById('thresholdSlider').value;
      
      const stream = document.getElementById('videoStream');
      const placeholder = document.getElementById('placeholder');
      const startBtn = document.getElementById('startBtn');
      const stopBtn = document.getElementById('stopBtn');
      const statusDot = document.getElementById('statusDot');
      const statusText = document.getElementById('statusText');
      
      detecting = true;
      placeholder.style.display = 'none';
      stream.style.display = 'block';
      startBtn.style.display = 'none';
      stopBtn.style.display = 'inline-flex';
      document.getElementById('recordBtn').disabled = false;
      
      if (statusDot) statusDot.className = 'status-dot active';
      if (statusText) statusText.textContent = 'Monitoring Active';
      window.addLog(`Started monitoring source: ${source} (Threshold: ${conf}%)`);

      if (source === 'webcam') {
          try {
              if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                  throw new Error("Camera API is blocked on this page context by your browser. Please make sure camera permission is allowed in your site settings.");
              }
              
              if (!window.currentFacingMode) window.currentFacingMode = 'environment';
              
              webcamStream = await navigator.mediaDevices.getUserMedia({ 
                  video: { width: 640, height: 360, facingMode: window.currentFacingMode } 
              });
              
              const webcamVideo = document.getElementById('webcamVideo');
              const detectionCanvas = document.getElementById('detectionCanvas');
              const flipBtn = document.getElementById('flipBtn');
              
              if (flipBtn) flipBtn.style.display = 'inline-flex';
              
              // Handle mirroring: only mirror if front camera ("user")
              if (window.currentFacingMode === 'user') {
                  webcamVideo.style.transform = 'scaleX(-1)';
                  detectionCanvas.style.transform = 'scaleX(-1)';
              } else {
                  webcamVideo.style.transform = 'scaleX(1)';
                  detectionCanvas.style.transform = 'scaleX(1)';
              }
              
              // Hide image feed and show live video/canvas overlay
              stream.style.display = 'none';
              webcamVideo.style.display = 'block';
              detectionCanvas.style.display = 'block';
              
              webcamVideo.srcObject = webcamStream;
              webcamVideo.autoplay = true;
              webcamVideo.playsInline = true;
              webcamVideo.muted = true;
              window.activeVideoElement = webcamVideo;
              
              try {
                  await webcamVideo.play();
              } catch (e) {
                  console.warn("webcamVideo.play() failed initially, retrying...", e);
              }
              
              // Initialize detection canvas sizing
              detectionCanvas.width = 640;
              detectionCanvas.height = 360;
              const canvasCtx = detectionCanvas.getContext('2d');
              
              const fps = 8; // 8 FPS for optimal real-time performance without queue lag
              const interval = 1000 / fps;
              let lastTime = 0;
              let isProcessingFrame = false; // Prevent HF server queue lag!
              
              const captureLoop = (timestamp) => {
                  if (!detecting) return;
                  
                  if (timestamp - lastTime >= interval) {
                      lastTime = timestamp;
                      
                      const vw = webcamVideo.videoWidth;
                      const vh = webcamVideo.videoHeight;
                      
                      if (vw > 0 && vh > 0 && !isProcessingFrame) {
                          isProcessingFrame = true;
                          
                          // Dynamically scale resolution while preserving aspect ratio! (Crucial for mobile portrait cameras)
                          const scale = Math.min(640 / vw, 640 / vh);
                          const targetW = Math.round(vw * scale);
                          const targetH = Math.round(vh * scale);
                          
                          // Use dynamic resolution so we don't squash mobile cameras
                          hiddenCanvas.width = targetW;
                          hiddenCanvas.height = targetH;
                          hiddenCtx.drawImage(webcamVideo, 0, 0, targetW, targetH);
                          
                          const dataUrl = hiddenCanvas.toDataURL('image/jpeg', 0.8); // 80% quality for better smoke detection
                          const threshold = document.getElementById('thresholdSlider').value / 100;
                          
                          fetch('/api/process_frame', {
                              method: 'POST',
                              headers: { 'Content-Type': 'application/json' },
                              body: JSON.stringify({ image: dataUrl, conf: threshold, return_image: false, session_id: window.sessionId })
                          })
                          .then(r => r.json())
                          .then(data => {
                              isProcessingFrame = false;
                              if (data.success && detecting) {
                                  // Update detection canvas to match the exact aspect ratio!
                                  if (detectionCanvas.width !== targetW || detectionCanvas.height !== targetH) {
                                      detectionCanvas.width = targetW;
                                      detectionCanvas.height = targetH;
                                  }
                                  
                                  // Clear detection canvas
                                  canvasCtx.clearRect(0, 0, targetW, targetH);
                                  
                                  // Draw neon premium bounding boxes locally in real-time
                                  if (data.detections && data.detections.length > 0) {
                                      data.detections.forEach(d => {
                                          // Coordinates match the dynamic resolution
                                          const x1 = d.bbox[0];
                                          const y1 = d.bbox[1];
                                          const x2 = d.bbox[2];
                                          const y2 = d.bbox[3];
                                          
                                          const w = x2 - x1;
                                          const h = y2 - y1;
                                          const isFire = d.class === 'Fire';
                                          
                                          canvasCtx.strokeStyle = isFire ? '#ff4d00' : '#8a90a0';
                                          canvasCtx.lineWidth = Math.max(2, Math.round(targetW / 150));
                                          canvasCtx.shadowColor = isFire ? 'rgba(255, 77, 0, 0.4)' : 'rgba(138, 144, 160, 0.3)';
                                          canvasCtx.shadowBlur = 8;
                                          
                                          // Bounding box
                                          canvasCtx.strokeRect(x1, y1, w, h);
                                          
                                          // Label tag
                                          canvasCtx.fillStyle = isFire ? '#ff4d00' : '#8a90a0';
                                          canvasCtx.shadowBlur = 0; // reset shadow for text
                                          const labelText = `${d.class} ${d.confidence.toFixed(0)}%`;
                                          canvasCtx.font = 'bold 12px Outfit, sans-serif';
                                          const textWidth = canvasCtx.measureText(labelText).width;
                                          
                                          canvasCtx.fillRect(x1 - 1, y1 - 20, textWidth + 12, 20);
                                          canvasCtx.fillStyle = '#ffffff';
                                          canvasCtx.fillText(labelText, x1 + 5, y1 - 6);
                                      });
                                  }
                                  
                                  document.getElementById('fpsVal').textContent = data.fps;
                                  document.getElementById('fireVal').textContent = (data.fire_conf * 100).toFixed(0) + '%';
                                  document.getElementById('smokeVal').textContent = (data.smoke_conf * 100).toFixed(0) + '%';
                                  
                                  const fireConfPct = data.fire_conf * 100;
                                  const smokeConfPct = data.smoke_conf * 100;
                                  
                                  if (fireConfPct > 0 || smokeConfPct > 0) {
                                      if (statusDot) statusDot.className = 'status-dot alert';
                                      if (statusText) statusText.textContent = '⚠ CRITICAL ALERT';
                                      window.playSiren();
                                      
                                      if (!window.lastAlertLogTime || Date.now() - window.lastAlertLogTime > 5000) {
                                          window.lastAlertLogTime = Date.now();
                                          window.addLog(`⚠ CRITICAL: Detected ${fireConfPct > 0 ? 'Fire (' + fireConfPct.toFixed(0) + '%)' : ''} ${smokeConfPct > 0 ? 'Smoke (' + smokeConfPct.toFixed(0) + '%)' : ''}`, true);
                                      }
                                  } else {
                                      if (statusDot) statusDot.className = 'status-dot active';
                                      if (statusText) statusText.textContent = 'Monitoring Active';
                                      window.stopSiren();
                                  }
                                  
                                  if (confidenceChart) {
                                      confidenceChart.data.datasets[0].data.shift();
                                      confidenceChart.data.datasets[0].data.push(fireConfPct);
                                      confidenceChart.data.datasets[1].data.shift();
                                      confidenceChart.data.datasets[1].data.push(smokeConfPct);
                                      confidenceChart.update();
                                  }
                                  
                                  window.loadAlertGallery();
                              }
                          })
                          .catch(err => {
                              isProcessingFrame = false;
                              console.error("Frame processing error:", err);
                          });
                      }
                  }
                  
                  webcamFrameId = requestAnimationFrame(captureLoop);
              };
              
              webcamFrameId = requestAnimationFrame(captureLoop);
          } catch (err) {
              console.error("Webcam access error:", err);
              window.addLog(`❌ Error: ${err.message}`, true);
              alert(`📷 Webcam Error:\nType: ${err.name}\nMessage: ${err.message}\n\nIf the browser blocked it, please click the lock/settings icon next to the URL bar and select "Allow" for Camera.`);
              window.stopStream();
          }
      } else {
          // Hide webcam elements and show image stream
          const webcamVideo = document.getElementById('webcamVideo');
          const detectionCanvas = document.getElementById('detectionCanvas');
          if (webcamVideo) webcamVideo.style.display = 'none';
          if (detectionCanvas) detectionCanvas.style.display = 'none';
          stream.style.display = 'block';
          
          stream.src = `/video_feed?source=${source}&conf=${conf}`;
          statsInterval = setInterval(updateStats, 1000);
      }
  };
 
  window.stopStream = () => {
      fetch('/stop').then(() => {
          const stream = document.getElementById('videoStream');
          const placeholder = document.getElementById('placeholder');
          const startBtn = document.getElementById('startBtn');
          const stopBtn = document.getElementById('stopBtn');
          const statusDot = document.getElementById('statusDot');
          const statusText = document.getElementById('statusText');
          
          stream.style.display = 'none';
          stream.src = '';
          placeholder.style.display = 'flex';
          startBtn.style.display = 'inline-flex';
          stopBtn.style.display = 'none';
          const flipBtn = document.getElementById('flipBtn');
          if (flipBtn) flipBtn.style.display = 'none';
          
          if (statusDot) statusDot.className = 'status-dot';
          if (statusText) statusText.textContent = 'System Ready';
          detecting = false;
          
          if (webcamStream) {
              webcamStream.getTracks().forEach(track => track.stop());
              webcamStream = null;
          }
          const webcamVideo = document.getElementById('webcamVideo');
          const detectionCanvas = document.getElementById('detectionCanvas');
          if (webcamVideo) {
              webcamVideo.pause();
              webcamVideo.srcObject = null;
              webcamVideo.style.display = 'none';
          }
          if (detectionCanvas) {
              const canvasCtx = detectionCanvas.getContext('2d');
              canvasCtx.clearRect(0, 0, 640, 360);
              detectionCanvas.style.display = 'none';
          }
          if (webcamFrameId) {
              cancelAnimationFrame(webcamFrameId);
              webcamFrameId = null;
          }
          
          if (mediaRecorder && mediaRecorder.state !== 'inactive') {
              mediaRecorder.stop();
          }
          document.getElementById('recordBtn').disabled = true;
          
          window.stopSiren();
          
          if (statsInterval) {
              clearInterval(statsInterval);
              statsInterval = null;
          }
          window.addLog("Monitoring stopped.");
      });
  };

  window.flipCamera = async () => {
      // Toggle facing mode
      window.currentFacingMode = (window.currentFacingMode === 'environment') ? 'user' : 'environment';
      window.addLog(`Switched camera to: ${window.currentFacingMode === 'environment' ? 'Rear' : 'Front'}`);
      
      // Stop current webcam tracks but keep session alive
      if (webcamStream) {
          webcamStream.getTracks().forEach(track => track.stop());
      }
      
      // Cancel previous rAF loops to prevent doubling
      if (webcamFrameId) {
          cancelAnimationFrame(webcamFrameId);
          webcamFrameId = null;
      }
      
      // Restart stream with new camera
      await window.startStream();
  };

  function updateStats() {
      if (!detecting) return;
      
      fetch('/stats').then(r => r.json()).then(data => {
          document.getElementById('fpsVal').textContent = data.fps;
          
          let fireConf = 0;
          let smokeConf = 0;
          
          if (data.recent_logs && data.recent_logs.length > 0) {
              const latest = data.recent_logs[data.recent_logs.length - 1];
              latest.detections.forEach(d => {
                  if (d.class === 'Fire' && d.confidence > fireConf) fireConf = d.confidence;
                  if (d.class === 'Smoke' && d.confidence > smokeConf) smokeConf = d.confidence;
              });
          }
          
          document.getElementById('fireVal').textContent = fireConf.toFixed(0) + '%';
          document.getElementById('smokeVal').textContent = smokeConf.toFixed(0) + '%';
          
          const statusDot = document.getElementById('statusDot');
          const statusText = document.getElementById('statusText');
          
          if (fireConf > 0 || smokeConf > 0) {
              if (statusDot) statusDot.className = 'status-dot alert';
              if (statusText) statusText.textContent = '⚠ CRITICAL ALERT';
              window.playSiren();
              window.addLog(`⚠ CRITICAL: Detected ${fireConf > 0 ? 'Fire (' + fireConf + '%)' : ''} ${smokeConf > 0 ? 'Smoke (' + smokeConf + '%)' : ''}`, true);
          } else {
              if (statusDot) statusDot.className = 'status-dot active';
              if (statusText) statusText.textContent = 'Monitoring Active';
              window.stopSiren();
          }
          
          // Update chart
          if (confidenceChart) {
              confidenceChart.data.datasets[0].data.shift();
              confidenceChart.data.datasets[0].data.push(fireConf);
              confidenceChart.data.datasets[1].data.shift();
              confidenceChart.data.datasets[1].data.push(smokeConf);
              confidenceChart.update();
          }
          
          window.loadAlertGallery();
      }).catch(() => {});
  }

  window.loadAlertGallery = () => {
      fetch(`/api/alerts?session_id=${window.sessionId}`).then(r => r.json()).then(data => {
          const countEl = document.getElementById('alertsCount');
          if (countEl) countEl.textContent = data.length;
          const gallery = document.getElementById('alertGallery');
          if (!gallery) return;
          if (data.length === 0) {
              gallery.innerHTML = '<div style="grid-column: span 2; text-align: center; padding: 2rem; color: var(--text-secondary); font-size: 0.8rem;">No captures saved yet.</div>';
              return;
          }
          
          gallery.innerHTML = data.slice(-6).reverse().map(filename => {
              const timeStr = filename.replace('alert_', '').replace('manual_', '').replace('.jpg', '').split('_')[1];
              const formattedTime = timeStr.slice(0,2) + ':' + timeStr.slice(2,4) + ':' + timeStr.slice(4,6);
              return `
                  <div class="alert-thumb" style="position: relative; border-radius: 8px; overflow: hidden; border: 1px solid var(--border-subtle); aspect-ratio: 16/10;">
                      <img src="/static/alerts/${window.sessionId}/${filename}" alt="Alert capture" style="width: 100%; height: 100%; object-fit: cover;">
                      <div class="time-tag" style="position: absolute; bottom: 0; inset-x: 0; background: rgba(0,0,0,0.7); font-size: 0.7rem; padding: 4px; text-align: center; color: var(--text-primary);"><i class="fas fa-clock"></i> ${formattedTime}</div>
                  </div>
              `;
          }).join('');
      });
  };

  window.toggleRecording = () => {
      const recordBtn = document.getElementById('recordBtn');
      const recordText = document.getElementById('recordText');
      const img = document.getElementById('videoStream');
      const canvas = document.getElementById('recordCanvas');
      const ctx = canvas.getContext('2d');
      
      if (!mediaRecorder || mediaRecorder.state === 'inactive') {
          recordedChunks = [];
          canvas.width = img.naturalWidth || 1280;
          canvas.height = img.naturalHeight || 720;
          
          function drawLoop() {
              if (detecting && img.style.display !== 'none') {
                  ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                  requestAnimationFrame(drawLoop);
              }
          }
          drawLoop();
          
          const stream = canvas.captureStream(30);
          mediaRecorder = new MediaRecorder(stream, { mimeType: 'video/webm;codecs=vp9' });
          
          mediaRecorder.ondataavailable = (e) => {
              if (e.data.size > 0) recordedChunks.push(e.data);
          };
          
          mediaRecorder.onstop = () => {
              const blob = new Blob(recordedChunks, { type: 'video/webm' });
              const url = URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = `firevision_recording_${new Date().toISOString().slice(0,19).replace(/:/g, '-')}.webm`;
              a.click();
              window.addLog("Session recording saved & downloaded.");
          };
          
          mediaRecorder.start();
          recordBtn.className = "btn-secondary";
          recordBtn.style.borderColor = "#ff3344";
          recordText.textContent = "Stop Recording";
          window.addLog("Session recording started.");
      } else {
          mediaRecorder.stop();
          recordBtn.className = "btn-secondary";
          recordBtn.style.borderColor = "var(--border-subtle)";
          recordText.textContent = "Record Session";
      }
  };

  window.generatePDFReport = async () => {
      const { jsPDF } = window.jspdf;
      const doc = new jsPDF();
      
      window.addLog("Generating PDF Safety Report...");
      
      doc.setFillColor(10, 10, 16);
      doc.rect(0, 0, 210, 297, 'F');
      
      doc.setTextColor(255, 77, 0);
      doc.setFontSize(24);
      doc.setFont('Helvetica', 'bold');
      doc.text("FIREVISION AI — SAFETY REPORT", 20, 30);
      
      doc.setTextColor(255, 255, 255);
      doc.setFontSize(10);
      doc.text(`Generated: ${new Date().toLocaleString()}`, 20, 40);
      doc.text("Prepared by: Nikhil Mali", 20, 46);
      
      doc.setDrawColor(255, 77, 0);
      doc.setLineWidth(1);
      doc.line(20, 52, 190, 52);
      
      const r = await fetch('/api/alerts');
      const files = await r.json();
      
      doc.setFontSize(14);
      doc.text("Detection Incident Logs:", 20, 65);
      
      let yOffset = 75;
      
      if (files.length === 0) {
          doc.setFontSize(12);
          doc.setTextColor(150, 150, 150);
          doc.text("No critical fire or smoke hazards detected during this session.", 20, yOffset);
      } else {
          const lastThree = files.slice(-3).reverse();
          for (let i = 0; i < lastThree.length; i++) {
              const file = lastThree[i];
              const timeStr = file.replace('alert_', '').replace('manual_', '').replace('.jpg', '').split('_')[1];
              const formattedTime = timeStr.slice(0,2) + ':' + timeStr.slice(2,4) + ':' + timeStr.slice(4,6);
              
              doc.setFontSize(10);
              doc.setTextColor(200, 200, 200);
              doc.text(`Incident #${i+1} — Captured at ${formattedTime}`, 20, yOffset);
              
              try {
                  const imgUrl = `/static/alerts/${file}`;
                  const base64Img = await getBase64ImageFromUrl(imgUrl);
                  doc.addImage(base64Img, 'JPEG', 20, yOffset + 5, 80, 50);
                  yOffset += 65;
              } catch(e) {
                  doc.text("[Image load error]", 20, yOffset + 10);
                  yOffset += 20;
              }
              
              if (yOffset > 240 && i < lastThree.length - 1) {
                  doc.addPage();
                  doc.setFillColor(10, 10, 16);
                  doc.rect(0, 0, 210, 297, 'F');
                  yOffset = 30;
              }
          }
      }
      
      doc.save(`FireVision_Safety_Report_${new Date().toISOString().slice(0,10)}.pdf`);
      window.addLog("PDF Safety Report downloaded.");
  };

  function getBase64ImageFromUrl(imageUrl) {
      return new Promise((resolve, reject) => {
          const img = new Image();
          img.setAttribute('crossOrigin', 'anonymous');
          img.onload = () => {
              const canvas = document.createElement('canvas');
              canvas.width = img.width;
              canvas.height = img.height;
              const ctx = canvas.getContext('2d');
              ctx.drawImage(img, 0, 0);
              const dataURL = canvas.toDataURL('image/jpeg');
              resolve(dataURL);
          };
          img.onerror = (error) => reject(error);
          img.src = imageUrl;
      });
  }

  window.handleFileSelect = (input) => {
      const uploadText = document.getElementById('uploadText');
      const processBtn = document.getElementById('processUploadBtn');
      if (input.files && input.files[0]) {
          uploadText.textContent = "Selected: " + input.files[0].name;
          processBtn.style.display = 'block';
      }
  };

  window.uploadAndProcess = () => {
      const formData = new FormData(document.getElementById('uploadForm'));
      formData.append("session_id", window.sessionId);
      window.addLog("Uploading file to server...");
      
      fetch('/upload', {
          method: 'POST',
          body: formData
      }).then(r => r.json()).then(data => {
          if (data.success) {
              window.addLog("File uploaded successfully. Initializing inference stream...");
              
              const select = document.getElementById('sourceSelect');
              let optionExists = false;
              for (let i=0; i<select.options.length; i++) {
                  if (select.options[i].value === data.filepath) {
                      optionExists = true;
                      break;
                  }
              }
              if (!optionExists) {
                  const opt = document.createElement('option');
                  opt.value = data.filepath;
                  opt.innerHTML = "🎬 Uploaded: " + data.filename;
                  select.appendChild(opt);
              }
              
              select.value = data.filepath;
              window.startStream();
          } else {
              alert("Upload failed: " + data.error);
          }
      });
  };

  window.triggerManualScreenshot = () => {
      fetch(`/screenshot?session_id=${window.sessionId}`).then(r => r.json()).then(data => {
          if (data.success) {
              window.addLog("Manual snapshot captured & saved.");
              window.loadAlertGallery();
          } else {
              alert("Snapshot failed: " + data.error);
          }
      });
  };

  // Load initial gallery
  window.loadAlertGallery();

  console.log(
    '%c🔥 Fire & Smoke Detection AI — Interface Loaded',
    'color:#ff6b35;font-size:14px;font-weight:bold;'
  );
});

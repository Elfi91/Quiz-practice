let isTimerPaused = false;
let timerEndTime = 0;
let timerPauseStart = 0;

document.addEventListener('DOMContentLoaded', () => {
    // Timer Logic
    const timerEl = document.getElementById('timer');
    if (timerEl) {
        timerEndTime = parseFloat(timerEl.dataset.end) * 1000; // Convert to ms
        const displayEl = document.getElementById('time-display');

        function updateTimer() {
            if (isTimerPaused) return;

            const now = Date.now();
            const diff = timerEndTime - now;

            if (diff <= 0) {
                displayEl.textContent = "00:00";
                // Time's up! Submit form
                const form = document.getElementById('quiz-form');
                if (form) {
                    form.submit();
                }
                return;
            }

            const minutes = Math.floor(diff / (1000 * 60));
            const seconds = Math.floor((diff % (1000 * 60)) / 1000);

            displayEl.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;

            // Warning style if < 5 mins
            if (minutes < 5) {
                timerEl.style.color = '#ef4444';
                timerEl.style.borderColor = '#ef4444';
            }
        }

        updateTimer(); // Init
        setInterval(updateTimer, 1000);
    }
});

// Global function controlled by quiz.html
window.toggleTimerPause = function () {
    isTimerPaused = !isTimerPaused;
    if (isTimerPaused) {
        timerPauseStart = Date.now();
    } else {
        // Add the paused duration to the end time
        const duration = Date.now() - timerPauseStart;
        timerEndTime += duration;
    }
};

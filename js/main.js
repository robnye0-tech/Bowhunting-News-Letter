document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector(".subscribe-form");
  if (!form) return;

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const email = form.querySelector("input[type=email]").value.trim();
    const note = form.querySelector(".form-note");
    if (email) {
      note.textContent = "Thanks — hook this form up to your email provider to start collecting subscribers.";
    }
  });
});

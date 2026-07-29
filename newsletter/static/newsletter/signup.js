document.addEventListener("DOMContentLoaded", () => {
  const MAX_STATES = 3;
  const checkboxes = Array.from(document.querySelectorAll('input[name="states"]'));
  const counter = document.querySelector(".state-count");
  if (!checkboxes.length || !counter) return;

  function update() {
    const checkedCount = checkboxes.filter((cb) => cb.checked).length;
    counter.textContent = `${checkedCount} of ${MAX_STATES} selected`;
    counter.classList.toggle("at-limit", checkedCount >= MAX_STATES);
    checkboxes.forEach((cb) => {
      if (!cb.checked) {
        cb.disabled = checkedCount >= MAX_STATES;
      }
    });
  }

  checkboxes.forEach((cb) => cb.addEventListener("change", update));
  update();
});

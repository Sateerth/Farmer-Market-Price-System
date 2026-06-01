// Crop chip selection
document.querySelectorAll(".crop-chip").forEach(chip => {
  chip.addEventListener("click", () => {
    chip.classList.toggle("selected");
    const cb = chip.querySelector("input[type=checkbox]");
    if (cb) cb.checked = !cb.checked;
  });
});

// Auto-dismiss alerts after 4s
setTimeout(() => {
  document.querySelectorAll(".alert.fade.show").forEach(el => {
    const bsAlert = bootstrap.Alert.getOrCreateInstance(el);
    bsAlert.close();
  });
}, 4000);
